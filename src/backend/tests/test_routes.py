from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.models import File, Service, ShareLink


def _make_mock():
    connector = AsyncMock()
    connector.get_service.return_value = Service(id="drive1", name="My Drive")
    connector.list_files.return_value = [
        File(
            id="file-001",
            name="hello.txt",
            type="file",
            mime_type="text/plain",
            path="/hello.txt",
            last_modified=datetime(2026, 1, 15, 10, 30, 0),
            creation_date=datetime(2026, 1, 10, 8, 0, 0),
            owner="alice",
            size=12,
        )
    ]
    connector.get_file.return_value = File(
        id="file-001",
        name="hello.txt",
        type="file",
        mime_type="text/plain",
        path="/hello.txt",
        last_modified=datetime(2026, 1, 15, 10, 30, 0),
        creation_date=datetime(2026, 1, 10, 8, 0, 0),
        owner="alice",
        size=12,
    )
    connector.get_share_link.return_value = ShareLink(
        url="https://twake.example/public?sharecode=abc123"
    )
    return connector


def _get_client(mock_connector):
    import app.api as api_module
    from app.main import app
    from fastapi.testclient import TestClient

    api_module.services = {"drive1": mock_connector}
    return TestClient(app)


def test_get_drive():
    mock = _make_mock()
    client = _get_client(mock)
    resp = client.get("/drive/drive1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "drive1"
    assert data["name"] == "My Drive"


def test_list_files():
    mock = _make_mock()
    client = _get_client(mock)
    resp = client.get("/drive/drive1/files?deep=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "hello.txt"


def test_list_files_default_deep():
    mock = _make_mock()
    client = _get_client(mock)
    resp = client.get("/drive/drive1/files")
    assert resp.status_code == 200


def test_get_file():
    mock = _make_mock()
    client = _get_client(mock)
    resp = client.get("/drive/drive1/files/file-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "file-001"


def test_get_share_link():
    mock = _make_mock()
    client = _get_client(mock)
    resp = client.get("/drive/drive1/files/file-001/share")
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data


def test_unknown_drive():
    mock = _make_mock()
    client = _get_client(mock)
    resp = client.get("/drive/unknown/files")
    assert resp.status_code == 404
