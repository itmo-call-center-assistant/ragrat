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

```bash
uv run fastapi dev src/indexer/app.py
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
