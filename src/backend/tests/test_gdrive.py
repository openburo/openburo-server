import pytest
from pytest_httpx import HTTPXMock

from app.connectors.gdrive import GDriveConnector
from app.models import File, Service, ShareLink


@pytest.fixture
def connector():
    return GDriveConnector(
        id="test",
        base_url="https://www.googleapis.com/drive/v3",
        token="test-token",
    )


@pytest.mark.asyncio
async def test_get_service(connector: GDriveConnector, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://www.googleapis.com/drive/v3/about?fields=user%28displayName%29",
        json={"user": {"displayName": "Test User"}},
    )
    service = await connector.get_service()
    assert isinstance(service, Service)
    assert service.id == "test"
    assert service.name == "Test User"


@pytest.mark.asyncio
async def test_list_files(connector: GDriveConnector, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        json={
            "files": [
                {
                    "id": "file-001",
                    "name": "doc.pdf",
                    "mimeType": "application/pdf",
                    "parents": ["root"],
                    "createdTime": "2026-01-10T08:00:00Z",
                    "modifiedTime": "2026-01-15T10:30:00Z",
                    "size": "204800",
                    "owners": [{"displayName": "Alice"}],
                }
            ]
        },
    )
    files = await connector.list_files(deep=0)
    assert len(files) == 1
    assert files[0].id == "file-001"
    assert files[0].name == "doc.pdf"
    assert files[0].mime_type == "application/pdf"
    assert files[0].owner == "Alice"
    assert files[0].size == 204800


@pytest.mark.asyncio
async def test_list_files_deep(connector: GDriveConnector, httpx_mock: HTTPXMock):
    # First call: root contains a folder
    httpx_mock.add_response(
        json={
            "files": [
                {
                    "id": "folder-001",
                    "name": "Subfolder",
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": ["root"],
                    "createdTime": "2026-01-10T08:00:00Z",
                    "modifiedTime": "2026-01-15T10:30:00Z",
                    "owners": [{"displayName": "Alice"}],
                }
            ]
        },
    )
    # Second call: subfolder contains a file
    httpx_mock.add_response(
        json={
            "files": [
                {
                    "id": "nested-file",
                    "name": "nested.txt",
                    "mimeType": "text/plain",
                    "parents": ["folder-001"],
                    "createdTime": "2026-01-10T08:00:00Z",
                    "modifiedTime": "2026-01-15T10:30:00Z",
                    "size": "42",
                    "owners": [{"displayName": "Alice"}],
                }
            ]
        },
    )
    files = await connector.list_files(deep=1)
    assert len(files) == 2
    assert files[0].id == "folder-001"
    assert files[0].type == "directory"
    assert files[1].id == "nested-file"
    assert files[1].type == "file"
    assert files[1].name == "nested.txt"


@pytest.mark.asyncio
async def test_get_file(connector: GDriveConnector, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        json={
            "id": "file-001",
            "name": "doc.pdf",
            "mimeType": "application/pdf",
            "parents": ["root"],
            "createdTime": "2026-01-10T08:00:00Z",
            "modifiedTime": "2026-01-15T10:30:00Z",
            "size": "204800",
            "owners": [{"displayName": "Alice"}],
        },
    )
    file = await connector.get_file("file-001")
    assert isinstance(file, File)
    assert file.id == "file-001"
    assert file.name == "doc.pdf"


@pytest.mark.asyncio
async def test_get_share_link(connector: GDriveConnector, httpx_mock: HTTPXMock):
    # First: create permission
    httpx_mock.add_response(
        json={"id": "anyoneWithLink", "type": "anyone", "role": "reader"},
    )
    # Second: get webViewLink
    httpx_mock.add_response(
        json={"webViewLink": "https://drive.google.com/file/d/file-001/view"},
    )
    link = await connector.get_share_link("file-001")
    assert isinstance(link, ShareLink)
    assert "drive.google.com" in link.url
