import httpx

from app.connectors.base import ServiceConnector
from app.models import File, Service, ShareLink

API_BASE = "https://www.googleapis.com/drive/v3"
FOLDER_MIME = "application/vnd.google-apps.folder"


class GDriveConnector(ServiceConnector):
    def __init__(self, id: str, base_url: str, token: str, verify_tls: bool = True):
        self.id = id
        self.base_url = base_url.rstrip("/") if base_url else API_BASE
        self.token = token
        self.verify_tls = verify_tls
        self.headers = {
            "Authorization": f"Bearer {token}",
        }

    async def get_service(self) -> Service:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/about",
                headers=self.headers,
                params={"fields": "user(displayName)"},
            )
            resp.raise_for_status()
            name = resp.json()["user"]["displayName"]
            return Service(id=self.id, name=name)

    async def list_files(self, deep: int = 0) -> list[File]:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            return await self._list_dir(client, "root", deep)

    async def _list_dir(
        self, client: httpx.AsyncClient, folder_id: str, deep: int
    ) -> list[File]:
        files: list[File] = []
        page_token = None

        while True:
            params = {
                "q": f"'{folder_id}' in parents and trashed=false",
                "fields": "nextPageToken,files(id,name,mimeType,parents,createdTime,modifiedTime,size,owners)",
                "pageSize": 1000,
            }
            if page_token:
                params["pageToken"] = page_token

            resp = await client.get(
                f"{self.base_url}/files",
                headers=self.headers,
                params=params,
            )
            resp.raise_for_status()
            body = resp.json()

            for item in body.get("files", []):
                if item["mimeType"] == FOLDER_MIME:
                    if deep > 0:
                        children = await self._list_dir(client, item["id"], deep - 1)
                        files.extend(children)
                else:
                    files.append(self._to_file(item))

            page_token = body.get("nextPageToken")
            if not page_token:
                break

        return files

    async def get_file(self, file_id: str) -> File:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/files/{file_id}",
                headers=self.headers,
                params={
                    "fields": "id,name,mimeType,parents,createdTime,modifiedTime,size,owners",
                },
            )
            resp.raise_for_status()
            return self._to_file(resp.json())

    async def get_share_link(self, file_id: str) -> ShareLink:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.post(
                f"{self.base_url}/files/{file_id}/permissions",
                headers=self.headers,
                json={"type": "anyone", "role": "reader"},
            )
            resp.raise_for_status()

            resp = await client.get(
                f"{self.base_url}/files/{file_id}",
                headers=self.headers,
                params={"fields": "webViewLink"},
            )
            resp.raise_for_status()
            return ShareLink(url=resp.json()["webViewLink"])

    def _to_file(self, item: dict) -> File:
        owners = item.get("owners", [])
        owner = owners[0]["displayName"] if owners else "unknown"
        parents = item.get("parents", [])
        path = f"/{'/'.join(parents)}/{item['name']}" if parents else f"/{item['name']}"
        return File(
            id=item["id"],
            name=item["name"],
            mime_type=item.get("mimeType", "application/octet-stream"),
            path=path,
            last_modified=item["modifiedTime"],
            creation_date=item["createdTime"],
            owner=owner,
            size=int(item.get("size", 0)),
        )
