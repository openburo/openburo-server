import pytest
from pytest_httpx import HTTPXMock

from openburo import OpenBuroClient, File, Service, ShareLink


@pytest.fixture
def client():
    return OpenBuroClient(base_url="https://api.example.com", token="test-token")


@pytest.mark.asyncio
async def test_get_drive(client: OpenBuroClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.example.com/drive/drive1",
        json={"id": "drive1", "name": "My Drive"},
    )
    service = await client.get_drive("drive1")
    assert isinstance(service, Service)
    assert service.id == "drive1"
    assert service.name == "My Drive"


@pytest.mark.asyncio
async def test_list_files(client: OpenBuroClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.example.com/drive/drive1/files?deep=0",
        json=[
            {
                "id": "file-001",
                "name": "hello.txt",
                "mime_type": "text/plain",
                "path": "/hello.txt",
                "last_modified": "2026-01-15T10:30:00Z",
                "creation_date": "2026-01-10T08:00:00Z",
                "owner": "alice",
                "size": 12,
            }
        ],
    )
    files = await client.list_files("drive1")
    assert len(files) == 1
    assert isinstance(files[0], File)
    assert files[0].name == "hello.txt"


@pytest.mark.asyncio
async def test_list_files_with_depth(client: OpenBuroClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.example.com/drive/drive1/files?deep=2",
        json=[],
    )
    files = await client.list_files("drive1", deep=2)
    assert files == []


@pytest.mark.asyncio
async def test_get_file(client: OpenBuroClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.example.com/drive/drive1/files/file-001",
        json={
            "id": "file-001",
            "name": "hello.txt",
            "mime_type": "text/plain",
            "path": "/hello.txt",
            "last_modified": "2026-01-15T10:30:00Z",
            "creation_date": "2026-01-10T08:00:00Z",
            "owner": "alice",
            "size": 12,
        },
    )
    file = await client.get_file("drive1", "file-001")
    assert isinstance(file, File)
    assert file.id == "file-001"


@pytest.mark.asyncio
async def test_get_share_link(client: OpenBuroClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.example.com/drive/drive1/files/file-001/share",
        json={"url": "https://example.com/share/abc123"},
    )
    link = await client.get_share_link("drive1", "file-001")
    assert isinstance(link, ShareLink)
    assert "abc123" in link.url


@pytest.mark.asyncio
async def test_auth_header(httpx_mock: HTTPXMock):
    client = OpenBuroClient(base_url="https://api.example.com", token="my-secret")
    httpx_mock.add_response(
        url="https://api.example.com/drive/d1",
        json={"id": "d1", "name": "Drive"},
    )
    await client.get_drive("d1")
    request = httpx_mock.get_requests()[0]
    assert request.headers["Authorization"] == "Bearer my-secret"


@pytest.mark.asyncio
async def test_no_auth_header(httpx_mock: HTTPXMock):
    client = OpenBuroClient(base_url="https://api.example.com")
    httpx_mock.add_response(
        url="https://api.example.com/drive/d1",
        json={"id": "d1", "name": "Drive"},
    )
    await client.get_drive("d1")
    request = httpx_mock.get_requests()[0]
    assert "Authorization" not in request.headers
