from fastapi import APIRouter

from .main import search as do_search
from .main import upsert, upsert_batch
from .models import (
    BatchUpsertRequest,
    BatchUpsertResponse,
    SearchRequest,
    SearchResult,
    UpsertRequest,
    UpsertResponse,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/search", response_model=list[SearchResult])
def search_endpoint(req: SearchRequest):
    return do_search(req.query, req.limit)


@router.post("/upsert", response_model=UpsertResponse)
def upsert_endpoint(req: UpsertRequest):
    upsert(req.text, req.document)
    return UpsertResponse()


@router.post("/upsert/batch", response_model=BatchUpsertResponse)
def batch_upsert_endpoint(req: BatchUpsertRequest):
    items = [{"text": i.text, "document": i.document} for i in req.items]
    upsert_batch(items)
    return BatchUpsertResponse(count=len(items))
