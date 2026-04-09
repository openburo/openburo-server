import asyncio
import base64
import json
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.connectors.base import ServiceConnector
from app.models import File, Service, ShareLink

ACTION = "token-api"
OAUTH_TOKEN_PATH = "/oauth2-server/token"
OAUTH_PROFILE_PATH = "/oauth2-server/me/profile"
TOKEN_REFRESH_MARGIN = 30  # seconds before expiry to trigger a refresh


class JamespotApiError(RuntimeError):
    """Raised when the Jamespot backend returns a non-zero error code."""

    def __init__(self, error: int, message: str | None):
        super().__init__(f"Jamespot API error {error}: {message or ''}")
        self.error = error
        self.message = message


def _decode_jwt_payload(token: str) -> dict:
    """Decode a JWT payload without verifying its signature."""
    parts = token.split(".")
    if len(parts) < 2:
        raise ValueError("invalid JWT: expected header.payload[.signature]")
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)  # base64url padding
    return json.loads(base64.urlsafe_b64decode(payload))


class JamespotConnector(ServiceConnector):
    """
    Connector for the Jamespot platform's filebank.

    Talks to the same endpoints as the jamespot-user-api JS library, but via
    the OAuth-protected `/token-api/{o}/{f}` action prefix instead of the
    cookie-protected `/api-front/`.

    The `token` field of the service config is a JWT whose payload contains
    `client_id`, `refresh_token` and (optionally) `client_secret`. The
    connector exchanges the refresh token for a short-lived access token via
    `/oauth2-server/token` and refreshes it on demand.
    """

    def __init__(self, id: str, base_url: str, token: str, verify_tls: bool = True):
        self.id = id
        self.base_url = base_url.rstrip("/")
        self.verify_tls = verify_tls

        claims = _decode_jwt_payload(token)
        client_id = claims.get("client_id")
        refresh_token = claims.get("refresh_token")
        if not client_id or not refresh_token:
            raise ValueError(
                "Jamespot JWT must contain `client_id` and `refresh_token` claims"
            )
        self.client_id = client_id
        self.client_secret = claims.get("client_secret") or ""
        self.refresh_token = refresh_token

        self._access_token: str | None = None
        self._access_token_expires_at: float = 0.0
        self._refresh_lock = asyncio.Lock()

    # ----- OAuth ------------------------------------------------------------

    async def _get_access_token(self, client: httpx.AsyncClient) -> str:
        if (
            self._access_token
            and time.monotonic() < self._access_token_expires_at - TOKEN_REFRESH_MARGIN
        ):
            return self._access_token

        async with self._refresh_lock:
            # Re-check after acquiring the lock to avoid duplicate refreshes.
            if (
                self._access_token
                and time.monotonic() < self._access_token_expires_at - TOKEN_REFRESH_MARGIN
            ):
                return self._access_token

            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
            }
            if self.client_secret:
                data["client_secret"] = self.client_secret

            resp = await client.post(
                f"{self.base_url}{OAUTH_TOKEN_PATH}",
                data=data,
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            body = resp.json()
            access = body.get("access_token")
            if not access:
                raise JamespotApiError(-1, f"no access_token in response: {body!r}")
            self._access_token = access
            expires_in = int(body.get("expires_in", 3600))
            self._access_token_expires_at = time.monotonic() + expires_in
            new_refresh = body.get("refresh_token")
            if new_refresh:
                self.refresh_token = new_refresh
            return access

    async def _auth_headers(self, client: httpx.AsyncClient) -> dict[str, str]:
        token = await self._get_access_token(client)
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    # ----- low-level helper -------------------------------------------------

    async def _call(
        self, client: httpx.AsyncClient, o: str, f: str, **params: Any
    ) -> Any:
        """POST to /token-api/{o}/{f} and unwrap the {error, result} envelope."""
        url = f"{self.base_url}/{ACTION}/{o}/{f}"
        headers = await self._auth_headers(client)
        resp = await client.post(url, headers=headers, json=params)
        resp.raise_for_status()
        body = resp.json()
        if body.get("error", 0) != 0:
            raise JamespotApiError(body.get("error", -1), body.get("errorMsg"))
        return body.get("result")

    # ----- ServiceConnector implementation ----------------------------------

    async def get_service(self) -> Service:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            headers = await self._auth_headers(client)
            resp = await client.get(
                f"{self.base_url}{OAUTH_PROFILE_PATH}",
                headers=headers,
            )
            resp.raise_for_status()
            profile = resp.json()
            # /me/profile shape may vary; fall back to anything that looks like a name.
            name = (
                profile.get("name")
                or profile.get("displayName")
                or profile.get("login")
                or profile.get("user", {}).get("name")
                if isinstance(profile, dict)
                else None
            )
            return Service(id=self.id, name=name or self.id)

    async def list_files(self, deep: int = 0) -> list[File]:
        """Root listing: one virtual directory per group (bank)."""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            banks = await self._call(client, "fileBank", "getBanks", format="raw-list")
            if not isinstance(banks, list) or not banks:
                return []
            files: list[File] = []
            for bank in banks:
                root = bank.get("rootFolder") or {}
                spot = bank.get("spot") or {}
                root_uri = root.get("uri")
                if not root_uri:
                    continue
                files.append(self._group_to_file(bank, spot, root, root_uri))
                if deep > 0:
                    files.extend(await self._list_dir(client, root_uri, deep - 1))
            return files

    async def list_folder(self, folder_id: str, deep: int = 0) -> list[File]:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            return await self._list_dir(client, self._decode_uri(folder_id), deep)

    async def _list_dir(
        self, client: httpx.AsyncClient, uri: str, deep: int
    ) -> list[File]:
        files: list[File] = []

        documents = await self._call(
            client, "fileBank", "getDocuments", parentURI=uri, format="raw-view"
        )
        for item in self._iter_results(documents):
            files.append(self._to_file(item))

        folders = await self._call(
            client, "fileBank", "getFolders", parentURI=uri, format="raw-list"
        )
        for folder in self._iter_results(folders):
            files.append(self._to_file(folder, force_type="directory"))
            if deep > 0:
                child_uri = folder.get("uri")
                if child_uri:
                    files.extend(await self._list_dir(client, child_uri, deep - 1))

        return files

    async def get_file(self, file_id: str) -> File:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            id_file = self._numeric_id_from(file_id)
            result = await self._call(
                client, "file", "get", idFile=id_file, format="raw-little"
            )
            return self._to_file(result)

    async def get_file_content(self, file_id: str) -> tuple[bytes, str]:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            id_file = self._numeric_id_from(file_id)
            result = await self._call(
                client, "file", "get", idFile=id_file, format="raw-little"
            )
            file_url = result.get("_url")
            if not file_url:
                raise JamespotApiError(-1, "file has no _url")
            absolute = (
                file_url
                if file_url.startswith("http")
                else urljoin(self.base_url + "/", file_url.lstrip("/"))
            )
            headers = await self._auth_headers(client)
            resp = await client.get(absolute, headers=headers, follow_redirects=True)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "application/octet-stream")
            return resp.content, content_type

    async def get_share_link(self, file_id: str) -> ShareLink:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            id_file = self._numeric_id_from(file_id)
            result = await self._call(
                client, "file", "get", idFile=id_file, format="raw-little"
            )
            file_url = result.get("_url") or ""
            absolute = (
                file_url
                if file_url.startswith("http")
                else urljoin(self.base_url + "/", file_url.lstrip("/"))
            )
            return ShareLink(url=absolute)

    # ----- helpers ----------------------------------------------------------

    # ----- ID encoding ------------------------------------------------------
    #
    # Jamespot URIs look like "rootFolder/551" or "file/123" — they contain a
    # slash, which collides with FastAPI path parameters in the route
    # /drive/{drive_id}/files/{file_id}/children. We expose URIs with the slash
    # replaced by a colon and decode them on the way back to the Jamespot API.

    @staticmethod
    def _encode_uri(uri: str) -> str:
        return uri.replace("/", ":")

    @staticmethod
    def _decode_uri(encoded: str) -> str:
        return encoded.replace(":", "/")

    @classmethod
    def _numeric_id_from(cls, file_id: str) -> int:
        """Extract the numeric id from an encoded URI like 'file:123' (or '123')."""
        decoded = cls._decode_uri(file_id)
        tail = decoded.rsplit("/", 1)[-1]
        return int(tail)

    @staticmethod
    def _iter_results(payload: Any) -> list[dict]:
        """The Jamespot envelopes vary: some return a list, some a paged dict."""
        if payload is None:
            return []
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("list", "items", "results", "data"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
        return []

    def _group_to_file(
        self, bank: dict, spot: dict, root: dict, root_uri: str
    ) -> File:
        """Represent a group/bank as a top-level virtual directory."""
        name = spot.get("title") or root.get("title") or root_uri
        created = (
            spot.get("dateCreation")
            or root.get("dateCreation")
            or bank.get("dateCreation")
        )
        modified = (
            spot.get("dateModified")
            or root.get("dateModified")
            or created
        )
        return File(
            id=self._encode_uri(root_uri),
            name=name,
            type="directory",
            mime_type="inode/directory",
            path=root_uri,
            last_modified=modified,
            creation_date=created,
            owner=spot.get("title") or "Jamespot",
            size=0,
        )

    def _to_file(self, item: dict, force_type: str | None = None) -> File:
        main_type = item.get("mainType", "")
        if force_type:
            ftype = force_type
        elif main_type in ("folder", "rootFolder") or item.get("type", "").lower().endswith("folder"):
            ftype = "directory"
        else:
            ftype = "file"

        uri = item.get("uri") or ""
        return File(
            id=self._encode_uri(uri) if uri else str(item.get("id", "")),
            name=item.get("title", ""),
            type=ftype,
            mime_type=item.get("mimetype", "application/octet-stream"),
            path=item.get("path") or uri,
            last_modified=item.get("dateModified") or item.get("dateCreation"),
            creation_date=item.get("dateCreation") or item.get("dateModified"),
            owner=(item.get("author") or {}).get("title", "unknown") if isinstance(item.get("author"), dict) else "unknown",
            size=int(item.get("size", 0) or 0),
        )
