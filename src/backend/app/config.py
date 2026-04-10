from pathlib import Path

import yaml

from app.connectors.base import ServiceConnector
from app.connectors.twake import TwakeConnector
from app.connectors.gdrive import GDriveConnector
from app.connectors.jamespot import JamespotConnector
from app.connectors.nextcloud import NextcloudConnector
from app.connectors.openburo import OpenBUROConnector

CONNECTOR_TYPES: dict[str, type[ServiceConnector]] = {
    "twake": TwakeConnector,
    "gdrive": GDriveConnector,
    "jamespot": JamespotConnector,
    "nextcloud": NextcloudConnector,
    "openburo": OpenBUROConnector,
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
        token=entry.get("token", ""),
        verify_tls=entry.get("verify_tls", True),
    )


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def load_services(config: dict) -> dict[str, ServiceConnector]:
    connectors: dict[str, ServiceConnector] = {}
    for entry in config.get("services", []):
        connectors[entry["id"]] = _build_connector(entry)
    return connectors


_config = _load_config()
services = load_services(_config)

server_meta = {
    "version": _config.get("version", "0.1.0"),
    "name": _config.get("name", "OpenBURO Router"),
    "capabilities": _config.get("capabilities", ["PICK", "BROWSE"]),
}
