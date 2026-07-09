"""Search endpoints — hybrid vector + BM25 search."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from application.search.service import SearchResponse, SearchService
from infrastructure.adapters.embeddings.local import LocalEmbeddingAdapter
from infrastructure.database import db

router = APIRouter()


def get_search_service() -> SearchService:
    """Dependency: build SearchService with local embedding adapter."""
    adapter = LocalEmbeddingAdapter()
    return SearchService(db, adapter)


@router.get("/")
async def search(
    q: str = Query(min_length=1, max_length=500),
    types: Optional[list[str]] = Query(None),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    organization_id: UUID = Query(
        ..., description="Organization ID for tenant isolation"
    ),
    search_service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    """Hybrid search across research objects.

    Combines semantic (vector) and keyword (BM25) search.
    Results are fused using Reciprocal Rank Fusion.
    """
    response = await search_service.search(
        query=q,
        organization_id=organization_id,
        types=types,
        limit=limit,
        offset=offset,
    )
    return response


@router.get("/suggestions")
async def suggestions(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=5, ge=1, le=10),
    organization_id: UUID = Query(
        ..., description="Organization ID for tenant isolation"
    ),
) -> list[str]:
    """Autocomplete suggestions using trigram similarity."""
    rows = await db.fetch_all(
        """
        SELECT title, similarity(title, $2) AS sim
        FROM nodes
        WHERE organization_id = $1
          AND deleted_at IS NULL
          AND title % $2
        ORDER BY sim DESC
        LIMIT $3
        """,
        organization_id,
        q,
        limit,
    )
    return [r["title"] for r in rows]
