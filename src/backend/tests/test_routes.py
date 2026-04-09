# tests/test_routes.py
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.models import File, Service, ShareLink


@pytest.fixture
def mock_connector():
    connector = AsyncMock()
    connector.get_service.return_value = Service(id="drive1", name="My Drive")
    connector.list_files.return_value = [
        File(
            id="file-001",
            name="hello.txt",
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


@pytest.fixture
def client(mock_connector):
    from app.main import app
    from app.api import get_connector

    app.dependency_overrides[get_connector] = lambda: mock_connector
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_drive(client, mock_connector):
    resp = client.get("/drive/drive1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "drive1"
    assert data["name"] == "My Drive"
    mock_connector.get_service.assert_called_once_with("drive1")


def test_list_files(client, mock_connector):
    resp = client.get("/drive/drive1/files?deep=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "hello.txt"
    mock_connector.list_files.assert_called_once_with("drive1", 2)


def test_list_files_default_deep(client, mock_connector):
    resp = client.get("/drive/drive1/files")
    assert resp.status_code == 200
    mock_connector.list_files.assert_called_once_with("drive1", 0)


def test_get_file(client, mock_connector):
    resp = client.get("/drive/drive1/files/file-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "file-001"
    mock_connector.get_file.assert_called_once_with("drive1", "file-001")


def test_get_share_link(client, mock_connector):
    resp = client.get("/drive/drive1/files/file-001/share")
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    mock_connector.get_share_link.assert_called_once_with("drive1", "file-001")
