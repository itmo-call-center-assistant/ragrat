from fastapi import APIRouter
from ragrat_shared.db import upsert

from .main import chunk_document
from .models import DocumentRequest, DocumentResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse)
def index_documents(req: DocumentRequest):
    all_chunks = []
    for item in req.items:
        chunks = chunk_document(item.text, item.document)
        all_chunks.extend(chunks)
    upsert(all_chunks)
    return DocumentResponse(chunks_created=len(all_chunks))
