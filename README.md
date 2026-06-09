# Quick start

Prepare development environment using [uv:](https://docs.astral.sh/uv/getting-started/installation/)

```sh
uv sync --all-packages && uv run pre-commit install
```

Start DB service using [podman](https://podman.io/docs/installation) (recommended) or docker:

```sh
uv run podman-compose up
```

Start indexer and worker services, upload demo data.

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_URL` | - | Qdrant server URL (required) |
| `QDRANT_API_KEY` | - | Qdrant API key (required) |
| `QDRANT_COLLECTION` | `DocumentChunks` | Qdrant collection name |
| `CHUNKING_DEFAULT_CHUNK_SIZE` | `1024` | Default chunk size |
| `EMBEDDING_MODEL` | `deepvk/USER2-base` | Embedding model |
| `LLM_API_KEY` | - | LLM API key (required) |
| `LLM_BASE_URL` | - | LLM base URL (required) |
| `LLM_MODEL` | - | LLM model name (required) |

## Indexer

FastAPI service for chunking documents and inserting into Qdrant.

```bash
uv run --env-file .env fastapi dev packages/indexer/src/app.py --port 8000
```

### Demo Upload CLI

Upload markdown documents to indexer:

```bash
uv run packages/demo-md-upload/main.py <source_dir> --indexer-url http://localhost:8000
```

## Worker

FastAPI service with WebRTC audio streaming and ASR.

```bash
uv run --env-file .env fastapi dev packages/worker/src/app.py --port 8001
```

See demo UI at [http://localhost:8001/ui](http://localhost:8001/ui)
