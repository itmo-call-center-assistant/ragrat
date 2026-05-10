from functools import lru_cache

import lancedb
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector

db_path = "./db/lancedb"
table_name = "document_chunks"
embedding_model = "distiluse-base-multilingual-cased-v1"

_embedder = get_registry().get("sentence-transformers").create(name=embedding_model)


class Schema(LanceModel):
    text: str = _embedder.SourceField()
    vector: Vector(_embedder.ndims()) = _embedder.VectorField()
    document: str


@lru_cache
def get_db():
    db = lancedb.connect(db_path)
    if table_name not in db.table_names():
        db.create_table(table_name, schema=Schema, mode="overwrite")
    return db


def get_table():
    return get_db().open_table(table_name)


def search(query: str, limit: int = 10) -> list[dict]:
    table = get_table()
    results = (
        table.search(query, query_type="hybrid", vector_column_name="vector", fts_columns="text")
        .limit(limit)
        .to_list()
    )
    return [
        {"text": r["text"], "document": r["document"], "distance": r.get("_distance")}
        for r in results
    ]


def search_batch(queries: list[str], limit: int = 10) -> list[list[dict]]:
    table = get_table()
    return [
        [
            {"text": r["text"], "document": r["document"], "distance": r.get("_distance")}
            for r in table.search(q, vector_column_name="vector").limit(limit).to_list()
        ]
        for q in queries
    ]


def upsert(text: str, document: str) -> None:
    table = get_table()
    table.add([{"text": text, "document": document}])
    table.create_fts_index("text", replace=True)


def upsert_batch(items: list[dict]) -> None:
    table = get_table()
    table.add(items)
    table.create_fts_index("text", replace=True)
