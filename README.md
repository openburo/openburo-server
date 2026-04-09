# Openburo-router

Drive proxy API with pluggable service connectors. Translates client requests into backend drive API calls.

## Setup

```bash
cd src/backend
uv sync
```

## Configuration

Copy `src/backend/services.example.yaml` to `src/backend/services.yaml` and configure your service instances:

```yaml
services:
  - id: mytwake
    type: twake
    url: https://your-instance.twake.example
    token: your-bearer-token
    verify_tls: true
```

The `id` is used in API paths (e.g. `/drive/mytwake/files`). To add more services, add entries to the list.

## Run

```bash
cd src/backend
uv run uvicorn app.main:app --reload
```

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/drive/{id}` | Fetch drive/service info |
| GET | `/drive/{id}/files?deep=x` | List files (recursive up to depth `x`) |
| GET | `/drive/{id}/files/{file_id}` | Fetch file metadata |
| GET | `/drive/{id}/files/{file_id}/share` | Generate share link |

## Docker

```bash
cd src/backend
docker build -t openburo .
docker run -p 8000:8000 -v ./services.yaml:/app/services.yaml openburo
```

## Tests

```bash
cd src/backend
uv run pytest
```
