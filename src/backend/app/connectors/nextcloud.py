import base64
import json
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from xml.etree import ElementTree as ET

import httpx

from app.connectors.base import ServiceConnector
from app.models import File, Service, ShareLink

DAV_NS = {"d": "DAV:", "oc": "http://owncloud.org/ns"}

PROPFIND_BODY = """<?xml version="1.0" encoding="UTF-8"?>
<d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
  <d:prop>
    <d:displayname/>
    <d:getlastmodified/>
    <d:getcontentlength/>
    <d:getcontenttype/>
    <d:resourcetype/>
    <d:creationdate/>
    <oc:fileid/>
    <oc:owner-display-name/>
  </d:prop>
</d:propfind>
"""


def _decode_jwt_payload(token: str) -> dict:
    """Decode the payload of a JWT *without* verifying its signature.

    The token is expected to embed `user` and `password` claims that the
    connector uses for WebDAV Basic auth.
    """
    parts = token.split(".")
    if len(parts) < 2:
        raise ValueError("invalid JWT: expected header.payload[.signature]")
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)  # base64url padding
    raw = base64.urlsafe_b64decode(payload)
    return json.loads(raw)


class NextcloudConnector(ServiceConnector):
    """
    Connector for Nextcloud's WebDAV API.

    The `token` field of the service config is a JWT whose payload contains
    `user` and `password` claims. We use them for HTTP Basic auth against
    `/remote.php/dav/files/{user}/...`.

    File and folder IDs are paths relative to the user's WebDAV root.
    """

    def __init__(self, id: str, base_url: str, token: str, verify_tls: bool = True):
        self.id = id
        self.base_url = base_url.rstrip("/")
        self.verify_tls = verify_tls

        claims = _decode_jwt_payload(token)
        user = claims.get("user") or claims.get("username") or claims.get("sub")
        password = claims.get("password") or claims.get("pass")
        if not user or not password:
            raise ValueError("Nextcloud JWT must contain `user` and `password` claims")
        self.user = user
        self.auth = httpx.BasicAuth(user, password)
        self.dav_root = f"{self.base_url}/remote.php/dav/files/{user}"

    # ----- ServiceConnector implementation ----------------------------------

    async def get_service(self) -> Service:
        # Nextcloud's user metadata via OCS provisioning API.
        async with httpx.AsyncClient(verify=self.verify_tls, auth=self.auth) as client:
            resp = await client.get(
                f"{self.base_url}/ocs/v2.php/cloud/users/{self.user}",
                headers={"OCS-APIRequest": "true", "Accept": "application/json"},
            )
            if resp.status_code == 200:
                data = resp.json().get("ocs", {}).get("data", {})
                name = data.get("displayname") or self.user
            else:
                name = self.user
            return Service(id=self.id, name=name)

    async def list_files(self, deep: int = 0) -> list[File]:
        return await self._list_path(path="", deep=deep)

    async def list_folder(self, folder_id: str, deep: int = 0) -> list[File]:
        return await self._list_path(path=folder_id, deep=deep)

    async def _list_path(self, path: str, deep: int) -> list[File]:
        async with httpx.AsyncClient(verify=self.verify_tls, auth=self.auth) as client:
            return await self._propfind_recursive(client, path, deep)

    async def _propfind_recursive(
        self, client: httpx.AsyncClient, path: str, deep: int
    ) -> list[File]:
        url = self._dav_url(path)
        resp = await client.request(
            "PROPFIND",
            url,
            headers={"Depth": "1", "Content-Type": "application/xml"},
            content=PROPFIND_BODY,
        )
        resp.raise_for_status()

        files: list[File] = []
        parent_href = self._href_path(url)
        for entry in self._parse_multistatus(resp.text):
            if entry["href_path"] == parent_href:
                # PROPFIND with Depth:1 includes the queried resource itself.
                continue
            files.append(self._to_file(entry))
            if entry["is_dir"] and deep > 0:
                child_path = entry["rel_path"]
                files.extend(
                    await self._propfind_recursive(client, child_path, deep - 1)
                )
        return files

    async def get_file(self, file_id: str) -> File:
        async with httpx.AsyncClient(verify=self.verify_tls, auth=self.auth) as client:
            url = self._dav_url(file_id)
            resp = await client.request(
                "PROPFIND",
                url,
                headers={"Depth": "0", "Content-Type": "application/xml"},
                content=PROPFIND_BODY,
            )
            resp.raise_for_status()
            entries = self._parse_multistatus(resp.text)
            if not entries:
                raise FileNotFoundError(file_id)
            return self._to_file(entries[0])

    async def get_file_content(self, file_id: str) -> tuple[bytes, str]:
        async with httpx.AsyncClient(verify=self.verify_tls, auth=self.auth) as client:
            resp = await client.get(self._dav_url(file_id), follow_redirects=True)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "application/octet-stream")
            return resp.content, content_type

    async def get_share_link(self, file_id: str) -> ShareLink:
        async with httpx.AsyncClient(verify=self.verify_tls, auth=self.auth) as client:
            resp = await client.post(
                f"{self.base_url}/ocs/v2.php/apps/files_sharing/api/v1/shares",
                headers={
                    "OCS-APIRequest": "true",
                    "Accept": "application/json",
                },
                data={
                    "path": "/" + file_id.lstrip("/"),
                    "shareType": "3",  # public link
                },
            )
            resp.raise_for_status()
            data = resp.json().get("ocs", {}).get("data", {})
            url = data.get("url")
            if not url:
                raise RuntimeError(f"Nextcloud share returned no url: {data!r}")
            return ShareLink(url=url)

    # ----- helpers ----------------------------------------------------------

    def _dav_url(self, path: str) -> str:
        clean = path.strip("/")
        if not clean:
            return self.dav_root + "/"
        return f"{self.dav_root}/{quote(clean)}"

    def _href_path(self, url: str) -> str:
        """Strip scheme/host so we can compare against `<d:href>` values."""
        from urllib.parse import urlparse

        return urlparse(url).path.rstrip("/")

    def _parse_multistatus(self, body: str) -> list[dict]:
        root = ET.fromstring(body)
        results: list[dict] = []
        dav_root_path = self._href_path(self.dav_root)
        for response in root.findall("d:response", DAV_NS):
            href_el = response.find("d:href", DAV_NS)
            if href_el is None or not href_el.text:
                continue
            href = href_el.text
            href_path = href.rstrip("/")

            propstat = response.find("d:propstat/d:prop", DAV_NS)
            if propstat is None:
                continue

            resource_type = propstat.find("d:resourcetype", DAV_NS)
            is_dir = (
                resource_type is not None
                and resource_type.find("d:collection", DAV_NS) is not None
            )

            from urllib.parse import unquote

            rel = unquote(href_path)
            if rel.startswith(dav_root_path):
                rel = rel[len(dav_root_path):]
            rel = rel.lstrip("/")

            results.append(
                {
                    "href_path": href_path,
                    "rel_path": rel,
                    "is_dir": is_dir,
                    "name": _text(propstat.find("d:displayname", DAV_NS))
                    or rel.rsplit("/", 1)[-1],
                    "size": int(_text(propstat.find("d:getcontentlength", DAV_NS)) or 0),
                    "mime": _text(propstat.find("d:getcontenttype", DAV_NS))
                    or ("inode/directory" if is_dir else "application/octet-stream"),
                    "last_modified": _parse_http_date(
                        _text(propstat.find("d:getlastmodified", DAV_NS))
                    ),
                    "creation_date": _parse_iso_date(
                        _text(propstat.find("d:creationdate", DAV_NS))
                    ),
                    "fileid": _text(propstat.find("oc:fileid", DAV_NS)) or rel,
                    "owner": _text(propstat.find("oc:owner-display-name", DAV_NS))
                    or self.user,
                }
            )
        return results

    def _to_file(self, entry: dict) -> File:
        last = entry["last_modified"] or datetime.fromtimestamp(0)
        created = entry["creation_date"] or last
        return File(
            id=entry["rel_path"],
            name=entry["name"],
            type="directory" if entry["is_dir"] else "file",
            mime_type=entry["mime"],
            path="/" + entry["rel_path"],
            last_modified=last,
            creation_date=created,
            owner=entry["owner"],
            size=entry["size"],
        )


def _text(el: ET.Element | None) -> str | None:
    return el.text if el is not None else None


def _parse_http_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


def _parse_iso_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
