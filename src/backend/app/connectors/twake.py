import httpx

from app.connectors.base import ServiceConnector
from app.models import File, Service, ShareLink

ROOT_DIR = "io.cozy.files.root-dir"


class TwakeConnector(ServiceConnector):
    def __init__(self, id: str, base_url: str, token: str, verify_tls: bool = True):
        self.id = id
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.verify_tls = verify_tls
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.api+json",
        }

    async def get_service(self) -> Service:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/settings/instance",
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            name = data["attributes"].get("public_name", "Twake")
            return Service(id=self.id, name=name)

    async def list_files(self, deep: int = 0) -> list[File]:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            return await self._list_dir(client, ROOT_DIR, deep)

    async def list_folder(self, folder_id: str, deep: int = 0) -> list[File]:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            return await self._list_dir(client, folder_id, deep)

    async def _list_dir(
        self, client: httpx.AsyncClient, dir_id: str, deep: int
    ) -> list[File]:
        resp = await client.get(
            f"{self.base_url}/files/{dir_id}",
            headers=self.headers,
        )
        resp.raise_for_status()
        body = resp.json()
        included = body.get("included", [])
        files: list[File] = []

        for item in included:
            attrs = item["attributes"]
            files.append(self._to_file(item))
            if attrs["type"] == "directory" and deep > 0:
                children = await self._list_dir(client, item["id"], deep - 1)
                files.extend(children)

        return files

    async def get_file(self, file_id: str) -> File:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/files/{file_id}",
                headers=self.headers,
            )
            resp.raise_for_status()
            return self._to_file(resp.json()["data"])

    async def get_file_content(self, file_id: str) -> tuple[bytes, str]:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/files/download/{file_id}",
                headers=self.headers,
                follow_redirects=True,
            )
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "application/octet-stream")
            return resp.content, content_type

    async def get_share_link(self, file_id: str) -> ShareLink:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            body = {
                "data": {
                    "type": "io.cozy.permissions",
                    "attributes": {
                        "permissions": {
                            "files": {
                                "type": "io.cozy.files",
                                "verbs": ["GET"],
                                "values": [file_id],
                            }
                        }
                    },
                }
            }
            resp = await client.post(
                f"{self.base_url}/permissions",
                headers={
                    **self.headers,
                    "Content-Type": "application/vnd.api+json",
                },
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            shortcodes = data["attributes"].get("shortcodes", {})
            code = next(iter(shortcodes.values()), "")
            url = f"{self.base_url}/public?sharecode={code}"
            return ShareLink(url=url)

    def _to_file(self, item: dict) -> File:
        attrs = item["attributes"]
        return File(
            id=item["id"],
            name=attrs["name"],
            type=attrs.get("type", "file"),
            mime_type=attrs.get("mime", "application/octet-stream"),
            path=attrs.get("path", ""),
            last_modified=attrs["updated_at"],
            creation_date=attrs["created_at"],
            owner=attrs.get("cozyMetadata", {}).get("createdByApp", "unknown"),
            size=attrs.get("size", 0),
        )
