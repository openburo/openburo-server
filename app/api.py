from fastapi import APIRouter, Depends, Query

from app.connectors.base import ServiceConnector
from app.connectors.cozy import CozyConnector
from app.config import settings
from app.models import File, Service, ShareLink

router = APIRouter()

_connector = CozyConnector(base_url=settings.cozy_url, token=settings.cozy_token)


def get_connector() -> ServiceConnector:
    return _connector


@router.get("/drive/{drive_id}", response_model=Service)
async def get_drive(
    drive_id: str,
    connector: ServiceConnector = Depends(get_connector),
):
    return await connector.get_service(drive_id)


@router.get("/drive/{drive_id}/files", response_model=list[File])
async def list_files(
    drive_id: str,
    deep: int = Query(default=0, ge=0),
    connector: ServiceConnector = Depends(get_connector),
):
    return await connector.list_files(drive_id, deep)


@router.get("/drive/{drive_id}/files/{file_id}", response_model=File)
async def get_file(
    drive_id: str,
    file_id: str,
    connector: ServiceConnector = Depends(get_connector),
):
    return await connector.get_file(drive_id, file_id)


@router.get("/drive/{drive_id}/files/{file_id}/share", response_model=ShareLink)
async def get_share_link(
    drive_id: str,
    file_id: str,
    connector: ServiceConnector = Depends(get_connector),
):
    return await connector.get_share_link(drive_id, file_id)
