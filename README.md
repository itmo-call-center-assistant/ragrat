# Quick start

```sh
uv sync && uv run pre-commit install
```

```sh
uv run podman-compose up
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `WEAVIATE_URL` | - | Weaviate server URL (required) |
| `WEAVIATE_API_KEY` | - | Weaviate API key (required) |
| `WEAVIATE_COLLECTION` | `DocumentChunks` | Weaviate collection name |
| `CHUNKING_DEFAULT_CHUNK_SIZE` | `1024` | Default chunk size |
| `EMBEDDING_MODEL` | `deepvk/USER2-base` | Embedding model |
| `EMBEDDING_POOLING` | `mean` | Embedding pooling |
| `OPENAI_API_KEY` | - | OpenAI API key (required) |
| `OPENAI_BASE_URL` | - | OpenAI base URL (required) |
| `OPENAI_MODEL` | - | OpenAI model name (required) |

## Indexer

FastAPI service for chunking documents and indexing into Weaviate.

### Run

```bash
uv run --env-file .env fastapi dev src/indexer/app.py --port 8000
```

## Worker

FastAPI service with WebRTC audio streaming and ASR.

### Run

```bash
uv run --env-file .env fastapi dev src/worker/app.py --port 8001
```

## Demo Upload CLI

Upload markdown documents to indexer:

```bash
uv run src/demo_md_upload/main.py <source_dir> --indexer-url http://localhost:8000
```
