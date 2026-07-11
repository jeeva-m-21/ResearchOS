"""Graph traversal endpoints — traverse edges between research nodes."""
from typing import Any, Optional
from uuid import UUID

from application.search.service import GraphTraversalResult, SearchService
from fastapi import APIRouter, Depends, Query
from infrastructure.adapters.embeddings.local import LocalEmbeddingAdapter
from infrastructure.database import db

router = APIRouter()


def get_search_service() -> SearchService:
    """Dependency: build SearchService with local embedding adapter."""
    adapter = LocalEmbeddingAdapter()
    return SearchService(db, adapter)


@router.get("/traverse")
async def traverse(
    node_id: UUID = Query(..., description="Starting node ID"),
    direction: str = Query("outgoing", regex="^(outgoing|incoming|both)$"),
    edge_type: Optional[str] = Query(None, description="Filter by edge type"),
    max_depth: int = Query(default=2, ge=1, le=5),
    limit: int = Query(default=20, ge=1, le=100),
    organization_id: UUID = Query(
        ..., description="Organization ID for tenant isolation"
    ),
    search_service: SearchService = Depends(get_search_service),
) -> list[dict[str, Any]]:
    """Traverse the research graph from a starting node.

    Returns all nodes reachable via edges within ``max_depth`` hops.
    Use ``direction`` to control traversal direction:
    - ``outgoing`` (default): follow edges from source to target
    - ``incoming``: follow edges from target to source
    - ``both``: follow edges in both directions

    Use ``edge_type`` to filter to a specific relationship type
    (e.g., ``tests``, ``references``, ``cites``).
    """
    results = await search_service.graph_search(
        node_id=node_id,
        organization_id=organization_id,
        direction=direction,
        edge_type=edge_type,
        max_depth=max_depth,
        limit=limit,
    )
    return [_traversal_to_dict(r) for r in results]


def _traversal_to_dict(r: GraphTraversalResult) -> dict[str, Any]:
    return {
        "source_id": str(r.source_id),
        "source_title": r.source_title,
        "source_type": r.source_type,
        "target_id": str(r.target_id),
        "target_title": r.target_title,
        "target_type": r.target_type,
        "edge_id": str(r.edge_id),
        "edge_type": r.edge_type,
        "direction": r.direction,
        "depth": r.depth,
    }
