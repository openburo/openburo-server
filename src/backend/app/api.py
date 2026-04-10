from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.config import services, server_meta, service_configs
from app.models import File, Service, ShareLink

router = APIRouter()


def get_connector(drive_id: str):
    connector = services.get(drive_id)
    if connector is None:
        raise HTTPException(status_code=404, detail=f"Unknown service: {drive_id}")
    return connector


@router.get("/.well-known/openburo/config.json")
async def wellknown_config():
    return {
        **server_meta,
        "services": service_configs,
    }


@router.get("/drive", response_model=list[Service])
async def list_drives():
    result = []
    for service_id, connector in services.items():
        result.append(Service(id=service_id, name=service_id))
    return result


@router.get("/drive/{drive_id}", response_model=Service)
async def get_drive(drive_id: str):
    return await get_connector(drive_id).get_service()


@router.get("/drive/{drive_id}/files", response_model=list[File])
async def list_files(drive_id: str, deep: int = Query(default=0, ge=0)):
    return await get_connector(drive_id).list_files(deep)


@router.get("/drive/{drive_id}/files/{file_id}", response_model=File)
async def get_file(drive_id: str, file_id: str):
    return await get_connector(drive_id).get_file(file_id)


@router.get("/drive/{drive_id}/files/{file_id}/children", response_model=list[File])
async def list_folder(
    drive_id: str, file_id: str, deep: int = Query(default=0, ge=0)
):
    return await get_connector(drive_id).list_folder(file_id, deep)


@router.get("/drive/{drive_id}/files/{file_id}/content")
async def get_file_content(drive_id: str, file_id: str):
    content, content_type = await get_connector(drive_id).get_file_content(file_id)
    return Response(content=content, media_type=content_type)


@router.get("/drive/{drive_id}/files/{file_id}/share", response_model=ShareLink)
async def get_share_link(drive_id: str, file_id: str):
    return await get_connector(drive_id).get_share_link(file_id)
