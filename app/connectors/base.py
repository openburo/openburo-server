from abc import ABC, abstractmethod

from app.models import File, Service, ShareLink


class ServiceConnector(ABC):
    @abstractmethod
    async def get_service(self, service_id: str) -> Service:
        ...

    @abstractmethod
    async def list_files(self, service_id: str, deep: int = 0) -> list[File]:
        ...

    @abstractmethod
    async def get_file(self, service_id: str, file_id: str) -> File:
        ...

    @abstractmethod
    async def get_share_link(self, service_id: str, file_id: str) -> ShareLink:
        ...
