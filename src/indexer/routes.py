from fastapi import APIRouter

from .main import upsert_document
from .models import DocumentRequest, DocumentResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse)
def index_documents(req: DocumentRequest):
    total_chunks = 0
    for item in req.items:
        total_chunks += upsert_document(item.text, item.document)
    return DocumentResponse(chunks_created=total_chunks)
