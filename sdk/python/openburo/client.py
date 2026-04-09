import httpx

from openburo.models import File, Service, ShareLink


class OpenBuroClient:
    """Async client for the OpenBURO router API."""

    def __init__(self, base_url: str, token: str | None = None, verify_ssl: bool = True):
        self.base_url = base_url.rstrip("/")
        self._headers: dict[str, str] = {}
        if token:
            self._headers["Authorization"] = f"Bearer {token}"
        self._verify = verify_ssl

    async def get_drive(self, drive_id: str) -> Service:
        data = await self._get(f"/drive/{drive_id}")
        return Service.model_validate(data)

    async def list_files(self, drive_id: str, deep: int = 0) -> list[File]:
        data = await self._get(f"/drive/{drive_id}/files", params={"deep": deep})
        return [File.model_validate(item) for item in data]

    async def get_file(self, drive_id: str, file_id: str) -> File:
        data = await self._get(f"/drive/{drive_id}/files/{file_id}")
        return File.model_validate(data)

    async def get_share_link(self, drive_id: str, file_id: str) -> ShareLink:
        data = await self._get(f"/drive/{drive_id}/files/{file_id}/share")
        return ShareLink.model_validate(data)

    async def _get(self, path: str, params: dict | None = None) -> dict | list:
        async with httpx.AsyncClient(verify=self._verify) as client:
            resp = await client.get(
                f"{self.base_url}{path}",
                headers=self._headers,
                params=params,
            )
            resp.raise_for_status()
            return resp.json()
