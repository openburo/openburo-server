# OpenBURO

Drive proxy API with pluggable service connectors. Translates client requests into backend drive API calls (currently Cozy-Stack).

## Setup

```bash
cd src/backend
uv sync
```

## Run

```bash
cd src/backend
uv run fastapi dev app/main.py
```

## Configuration

Copy `src/backend/.env.example` to `src/backend/.env` and set:

| Variable | Purpose |
|----------|---------|
| `COZY_URL` | Base URL of the Cozy-Stack instance |
| `COZY_TOKEN` | Authentication token for Cozy-Stack |

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/drive/{id}` | Fetch drive/service info |
| GET | `/drive/{id}/files?deep=x` | List files (recursive up to depth `x`) |
| GET | `/drive/{id}/files/{file_id}` | Fetch file metadata |
| GET | `/drive/{id}/files/{file_id}/share` | Generate share link |

## Tests

```bash
cd src/backend
uv run pytest
```
