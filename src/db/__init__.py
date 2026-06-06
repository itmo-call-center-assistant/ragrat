from functools import lru_cache

import weaviate
from weaviate.classes.config import Configure
from weaviate.classes.init import Auth

from config import settings


@lru_cache
def get_client() -> weaviate.WeaviateClient:
    return weaviate.connect_to_custom(
        http_host=settings.weaviate.host,
        http_port=11480,
        http_secure=False,
        grpc_host=settings.weaviate.host,
        grpc_port=50051,
        grpc_secure=False,
        auth_credentials=Auth.api_key(settings.weaviate.api_key),
    )


def get_collection():
    client = get_client()
    if not client.collections.exists(settings.weaviate.collection):
        collection = client.collections.create(
            name=settings.weaviate.collection,
            vector_config=[
                Configure.Vectors.text2vec_transformers(
                    name="text_vector", source_properties=["text"]
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
    else:
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
