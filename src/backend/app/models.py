from datetime import datetime

from pydantic import BaseModel


class Service(BaseModel):
    id: str
    name: str


class File(BaseModel):
    id: str
    name: str
    type: str  # "file" or "directory"
    mime_type: str
    path: str
    last_modified: datetime
    creation_date: datetime
    owner: str
    size: int


class ShareLink(BaseModel):
    url: str
