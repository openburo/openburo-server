from datetime import datetime

from app.models import File, Service


def test_service_model():
    service = Service(id="abc123", name="My Drive")
    assert service.id == "abc123"
    assert service.name == "My Drive"


def test_file_model():
    file = File(
        id="file-001",
        name="report.pdf",
        type="file",
        mime_type="application/pdf",
        path="/Documents/report.pdf",
        last_modified=datetime(2026, 1, 15, 10, 30, 0),
        creation_date=datetime(2026, 1, 10, 8, 0, 0),
        owner="alice",
        size=204800,
    )
    assert file.id == "file-001"
    assert file.name == "report.pdf"
    assert file.mime_type == "application/pdf"
    assert file.path == "/Documents/report.pdf"
    assert file.size == 204800


def test_file_model_serialization():
    file = File(
        id="file-001",
        name="report.pdf",
        type="file",
        mime_type="application/pdf",
        path="/Documents/report.pdf",
        last_modified=datetime(2026, 1, 15, 10, 30, 0),
        creation_date=datetime(2026, 1, 10, 8, 0, 0),
        owner="alice",
        size=204800,
    )
    data = file.model_dump()
    assert data["mime_type"] == "application/pdf"
    assert "id" in data
