from abc import ABC, abstractmethod

from app.models import File, Service, ShareLink


class ServiceConnector(ABC):
    @abstractmethod
    async def get_service(self) -> Service:
        ...

    @abstractmethod
    async def list_files(self, deep: int = 0) -> list[File]:
        ...

    @abstractmethod
    async def list_folder(self, folder_id: str, deep: int = 0) -> list[File]:
        ...

    @abstractmethod
    async def get_file(self, file_id: str) -> File:
        ...

    @abstractmethod
    async def get_share_link(self, file_id: str) -> ShareLink:
        ...
