from pathlib import Path

import yaml

from app.connectors.base import ServiceConnector
from app.connectors.twake import TwakeConnector
from app.connectors.gdrive import GDriveConnector

CONNECTOR_TYPES: dict[str, type[ServiceConnector]] = {
    "twake": TwakeConnector,
    "gdrive": GDriveConnector,
}

CONFIG_PATH = Path(__file__).resolve().parent.parent / "services.yaml"


def _build_connector(entry: dict) -> ServiceConnector:
    connector_type = entry["type"]
    cls = CONNECTOR_TYPES.get(connector_type)
    if cls is None:
        raise ValueError(f"Unknown service type: {connector_type}")
    return cls(
        id=entry["id"],
        base_url=entry["url"],
        token=entry["token"],
        verify_tls=entry.get("verify_tls", True),
    )


def load_services() -> dict[str, ServiceConnector]:
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    connectors: dict[str, ServiceConnector] = {}
    for entry in config["services"]:
        connectors[entry["id"]] = _build_connector(entry)
    return connectors


services = load_services()
