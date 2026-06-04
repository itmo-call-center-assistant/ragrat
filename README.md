# Quick start

```sh
uv sync && uv run pre-commit install
```

```sh
uv run podman-compose up
```

## Indexer

FastAPI service for chunking documents and indexing into Weaviate.

### Run

```sh
uv run podman compose up
```

```bash
uv run --env-file .env fastapi dev src/indexer/app.py
```

### Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `WEAVIATE_URL` | `http://localhost:11480` | Weaviate server URL |
| `WEAVIATE_API_KEY` | `secr3t` | Weaviate API key |
| `WEAVIATE_COLLECTION` | `DocumentChunks` | Weaviate collection name |
| `CHUNKING_DEFAULT_CHUNK_SIZE` | `1024` | Default chunk size |
| `CHUNKING_LANG` | `en` | Language for chunking |
| `EMBEDDING_MODEL` | `deepvk/USER2-base` | Embedding model |
| `EMBEDDING_POOLING` | `mean` | Embedding pooling |

## Demo Upload CLI

Upload markdown documents to indexer:

```bash
uv run src/demo_md_upload/main.py <source_dir> --indexer-url http://localhost:8000
```
