import re

from chonkie import Pipeline, TableChunker

from config import settings
from db import get_collection

LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def strip_links(text: str) -> str:
    return LINK_PATTERN.sub(r"\1", text)


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
