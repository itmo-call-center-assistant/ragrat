import re
from functools import lru_cache

import weaviate
from chonkie import Pipeline, TableChunker
from weaviate.auth import AuthApiKey

from config import settings

LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def strip_links(text: str) -> str:
    return LINK_PATTERN.sub(r"\1", text)


@lru_cache
def get_client() -> weaviate.WeaviateClient:
    return weaviate.WeaviateClient(
        connection_params=weaviate.connect.base.ConnectionParams.from_url(
            settings.weaviate.url, 9091
        ),
        auth_client_secret=AuthApiKey(settings.weaviate.api_key),
    )


def get_collection():
    client = get_client()
    collection = client.collections.get(settings.weaviate.collection)
    if collection is None:
        client.collections.create(
            name=settings.weaviate.collection,
            vectorizer_config=[
                weaviate.classes.config.NamedVectors.text2_vec_transformers(
                    name="text_vector",
                    source_properties=["text"],
                    vectorizer_collection_config=weaviate.classes.config.VectorizerConfig(
                        model=settings.embedding.model,
                        pooling=settings.embedding.pooling,
                    ),
                )
            ],
            properties=[
                weaviate.classes.config.Property(
                    name="text", data_type=weaviate.classes.config.DataType.TEXT
                ),
                weaviate.classes.config.Property(
                    name="document", data_type=weaviate.classes.config.DataType.TEXT
                ),
            ],
        )
        collection = client.collections.get(settings.weaviate.collection)
    return collection


def chunk_text(text: str, chunk_size: int | None = None) -> list[str]:
    size = chunk_size or settings.chunking.default_chunk_size
    text = strip_links(text)

    table_chunker = TableChunker(tokenizer="row", chunk_size=5)

    doc = (
        Pipeline().process_with("markdown").chunk_with("recursive", chunk_size=size).run(texts=text)
    )

    chunks = []
    for chunk in doc.chunks:
        chunks.append(chunk.text)

    for table in doc.tables:
        for chunk in table_chunker.chunk(table.content):
            chunks.append(chunk.text)

    return chunks


def upsert_document(text: str, document: str) -> int:
    chunks = chunk_text(text)
    collection = get_collection()

    objects = [{"text": chunk, "document": document} for chunk in chunks]

    collection.data.insert_many(objects)
    return len(chunks)


def search(query: str, limit: int = 10) -> list[dict]:
    collection = get_collection()
    results = collection.query.near_text(
        query=query,
        limit=limit,
        return_properties=["text", "document"],
    )
    chunks = []
    for obj in results.objects:
        chunks.append(
            {
                "text": obj.properties["text"],
                "document": obj.properties["document"],
                "distance": obj.metadata.distance,
            }
        )
    return chunks
