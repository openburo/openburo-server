import httpx

from app.connectors.base import ServiceConnector
from app.models import File, Service, ShareLink


class OpenBUROConnector(ServiceConnector):
    """Connector for remote OpenBURO-certified services."""

    def __init__(self, id: str, base_url: str, token: str = "", verify_tls: bool = True):
        self.id = id
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.verify_tls = verify_tls
        self.headers: dict[str, str] = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        self._drive_endpoint: str | None = None

    async def _get_drive_base(self) -> str:
        if self._drive_endpoint is not None:
            return self._drive_endpoint

        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/.well-known/openburo/config.json",
                headers=self.headers,
            )
            resp.raise_for_status()
            config = resp.json()
            drive_path = config["endpoints"]["drive"]
            self._drive_endpoint = f"{self.base_url}{drive_path}"
            return self._drive_endpoint

    async def get_service(self) -> Service:
        drive_base = await self._get_drive_base()
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/.well-known/openburo/config.json",
                headers=self.headers,
            )
            resp.raise_for_status()
            config = resp.json()
            return Service(id=self.id, name=config.get("name", self.id))

    async def list_files(self, deep: int = 0) -> list[File]:
        drive_base = await self._get_drive_base()
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{drive_base}/files",
                headers=self.headers,
                params={"deep": deep},
            )
            resp.raise_for_status()
            return [File(**f) for f in resp.json()]

    async def list_folder(self, folder_id: str, deep: int = 0) -> list[File]:
        drive_base = await self._get_drive_base()
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{drive_base}/files/{folder_id}/children",
                headers=self.headers,
                params={"deep": deep},
            )
            resp.raise_for_status()
            return [File(**f) for f in resp.json()]

    async def get_file(self, file_id: str) -> File:
        drive_base = await self._get_drive_base()
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{drive_base}/files/{file_id}",
                headers=self.headers,
            )
            resp.raise_for_status()
            return File(**resp.json())

    async def get_file_content(self, file_id: str) -> tuple[bytes, str]:
        drive_base = await self._get_drive_base()
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{drive_base}/files/{file_id}/content",
                headers=self.headers,
                follow_redirects=True,
            )
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "application/octet-stream")
            return resp.content, content_type

    async def get_share_link(self, file_id: str) -> ShareLink:
        drive_base = await self._get_drive_base()
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{drive_base}/files/{file_id}/share",
                headers=self.headers,
            )
            resp.raise_for_status()
            return ShareLink(**resp.json())
