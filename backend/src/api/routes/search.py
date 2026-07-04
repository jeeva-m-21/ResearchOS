"""Search endpoints"""
from fastapi import APIRouter, Query
from typing import Optional, List

router = APIRouter()

@router.get("/")
async def search(
    q: str = Query(min_length=1, max_length=500),
    types: Optional[List[str]] = Query(None),
    limit: int = Query(default=10, ge=1, le=100),
):
    """Hybrid search across research objects"""
    # TODO: Implement
    return {
        "results": [],
        "total": 0,
        "query": q
    }
