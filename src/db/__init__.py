from functools import lru_cache

import weaviate
from weaviate.auth import AuthApiKey

from config import settings


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
