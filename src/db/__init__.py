import uuid
from functools import lru_cache

from fastembed import TextEmbedding
from fastembed.common.model_description import ModelSource, PoolingType
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    Document,
    Fusion,
    FusionQuery,
    Modifier,
    PointStruct,
    Prefetch,
    SparseVectorParams,
    VectorParams,
)

from config import settings

embedding_dim = 768
TextEmbedding.add_custom_model(
    model=settings.embedding.model,
    pooling=PoolingType.MEAN,
    normalization=True,
    sources=ModelSource(hf=settings.embedding.model),
    dim=embedding_dim,
)
embedding_model = TextEmbedding(model_name=settings.embedding.model)


@lru_cache
def get_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant.url)


def get_bm25(text: str) -> Document:
    return Document(text=text, model="Qdrant/bm25", options={"language": "russian"})


def ensure_collection() -> None:
    client = get_client()
    collection_name = settings.qdrant.collection
    if not client.collection_exists(collection_name=collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense_text": VectorParams(size=embedding_dim, distance=Distance.COSINE),
            },
            sparse_vectors_config={"bm25_text": SparseVectorParams(modifier=Modifier.IDF)},
        )


def search(query: str, limit: int = 10) -> list[dict]:
    ensure_collection()
    client = get_client()

    query_vector = next(embedding_model.embed(query))

    results = client.query_points(
        collection_name=settings.qdrant.collection,
        prefetch=[
            Prefetch(
                query=get_bm25(query),
                using="bm25_text",
                limit=limit,
            ),
            Prefetch(
                query=query_vector,
                using="dense_text",
                limit=limit,
            ),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=limit,
        with_payload=["text", "document"],  # Only return these specific fields
    )

    # 3. Format the results
    chunks = []
    for hit in results.points:
        chunks.append(
            {
                "text": hit.payload.get("text"),
                "document": hit.payload.get("document"),
            }
        )
    return chunks


def upsert(items: list[dict]) -> None:
    ensure_collection()
    client = get_client()

    points = []
    for i, vector in enumerate(embedding_model.embed(item["text"] for item in items)):
        item = items[i]
        bm25_vector = get_bm25(item["text"])
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector={"dense_text": vector, "bm25_text": bm25_vector},
                payload={"text": item["text"], "document": item["document"]},
            )
        )

    # 3. Upload to Qdrant
    client.upsert(collection_name=settings.qdrant.collection, points=points)
