# Openburo-router

Drive proxy API with pluggable service connectors. Translates client requests into backend drive API calls (currently Twake Drive).

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
| `TWAKE_URL` | Base URL of the Twake Drive instance |
| `TWAKE_TOKEN` | Authentication token for Twake Drive |

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
docker run -p 8000:8000 -e TWAKE_URL=https://your-instance.twake.example -e TWAKE_TOKEN=your-token openburo
```

## Tests

```bash
cd src/backend
uv run pytest
```
