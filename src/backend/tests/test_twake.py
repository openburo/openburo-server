import pytest
from pytest_httpx import HTTPXMock

from app.connectors.twake import TwakeConnector
from app.models import File, Service, ShareLink


@pytest.fixture
def connector():
    return TwakeConnector(id="test", base_url="https://test.twake.example", token="test-token")


@pytest.mark.asyncio
async def test_get_service(connector: TwakeConnector, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://test.twake.example/settings/instance",
        json={
            "data": {
                "type": "io.cozy.settings",
                "id": "io.cozy.settings.instance",
                "attributes": {"public_name": "My Twake"},
            }
        },
    )
    service = await connector.get_service()
    assert isinstance(service, Service)
    assert service.name == "My Twake"


@pytest.mark.asyncio
async def test_list_files(connector: TwakeConnector, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://test.twake.example/files/io.cozy.files.root-dir",
        json={
            "data": {
                "type": "io.cozy.files",
                "id": "root-dir-id",
                "attributes": {
                    "type": "directory",
                    "name": "Documents",
                    "path": "/Documents",
                    "created_at": "2026-01-10T08:00:00Z",
                    "updated_at": "2026-01-15T10:30:00Z",
                },
                "relationships": {
                    "contents": {
                        "data": [
                            {"type": "io.cozy.files", "id": "file-001"},
                        ]
                    }
                },
            },
            "included": [
                {
                    "type": "io.cozy.files",
                    "id": "file-001",
                    "attributes": {
                        "type": "file",
                        "name": "hello.txt",
                        "path": "/Documents/hello.txt",
                        "mime": "text/plain",
                        "size": 12,
                        "created_at": "2026-01-10T08:00:00Z",
                        "updated_at": "2026-01-15T10:30:00Z",
                    },
                }
            ],
        },
    )
    files = await connector.list_files(deep=0)
    assert len(files) == 1
    assert files[0].id == "file-001"
    assert files[0].name == "hello.txt"
    assert files[0].mime_type == "text/plain"


@pytest.mark.asyncio
async def test_list_files_deep_recursion(connector: TwakeConnector, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://test.twake.example/files/io.cozy.files.root-dir",
        json={
            "data": {
                "type": "io.cozy.files",
                "id": "root-dir-id",
                "attributes": {
                    "type": "directory",
                    "name": "Documents",
                    "path": "/Documents",
                    "created_at": "2026-01-10T08:00:00Z",
                    "updated_at": "2026-01-15T10:30:00Z",
                },
            },
            "included": [
                {
                    "type": "io.cozy.files",
                    "id": "subdir-001",
                    "attributes": {
                        "type": "directory",
                        "name": "Sub",
                        "path": "/Documents/Sub",
                        "created_at": "2026-01-10T08:00:00Z",
                        "updated_at": "2026-01-15T10:30:00Z",
                    },
                }
            ],
        },
    )
    httpx_mock.add_response(
        url="https://test.twake.example/files/subdir-001",
        json={
            "data": {
                "type": "io.cozy.files",
                "id": "subdir-001",
                "attributes": {
                    "type": "directory",
                    "name": "Sub",
                    "path": "/Documents/Sub",
                    "created_at": "2026-01-10T08:00:00Z",
                    "updated_at": "2026-01-15T10:30:00Z",
                },
            },
            "included": [
                {
                    "type": "io.cozy.files",
                    "id": "nested-file",
                    "attributes": {
                        "type": "file",
                        "name": "nested.txt",
                        "path": "/Documents/Sub/nested.txt",
                        "mime": "text/plain",
                        "size": 5,
                        "created_at": "2026-01-10T08:00:00Z",
                        "updated_at": "2026-01-15T10:30:00Z",
                    },
                }
            ],
        },
    )
    files = await connector.list_files(deep=1)
    assert len(files) == 2
    assert files[0].id == "subdir-001"
    assert files[0].type == "directory"
    assert files[1].id == "nested-file"
    assert files[1].type == "file"


@pytest.mark.asyncio
async def test_get_file(connector: TwakeConnector, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://test.twake.example/files/file-001",
        json={
            "data": {
                "type": "io.cozy.files",
                "id": "file-001",
                "attributes": {
                    "type": "file",
                    "name": "hello.txt",
                    "path": "/Documents/hello.txt",
                    "mime": "text/plain",
                    "size": 12,
                    "created_at": "2026-01-10T08:00:00Z",
                    "updated_at": "2026-01-15T10:30:00Z",
                },
            }
        },
    )
    file = await connector.get_file("file-001")
    assert isinstance(file, File)
    assert file.id == "file-001"
    assert file.name == "hello.txt"


@pytest.mark.asyncio
async def test_get_share_link(connector: TwakeConnector, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://test.twake.example/permissions",
        method="POST",
        json={
            "data": {
                "id": "perm-001",
                "type": "io.cozy.permissions",
                "attributes": {
                    "type": "share",
                    "codes": {"share": "abc123code"},
                    "shortcodes": {"share": "shortABC"},
                },
            }
        },
    )
    link = await connector.get_share_link("file-001")
    assert isinstance(link, ShareLink)
    assert "shortABC" in link.url
