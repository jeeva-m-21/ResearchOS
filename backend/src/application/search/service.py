"""Hybrid search service combining vector similarity and BM25."""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID


@dataclass
class SearchResult:
    """A single search result."""

    id: UUID
    node_type: str
    title: str
    description: Optional[str]
    score: float
    highlights: list[str] = field(default_factory=list)


@dataclass
class SearchResponse:
    """Full search response."""

    results: list[SearchResult] = field(default_factory=list)
    total: int = 0
    took_ms: int = 0
    query: str = ""


class SearchService:
    """Hybrid search over the nodes table.

    Combines:
    1. Vector (semantic) search via pgvector cosine similarity
    2. BM25 (keyword) search via PostgreSQL tsvector
    3. Reciprocal Rank Fusion for final ranking
    """

    def __init__(self, db: Any, embedding_adapter: Any, rrf_k: int = 60):
        self.db = db
        self.embedding = embedding_adapter
        self.rrf_k = rrf_k

    async def search(
        self,
        query: str,
        organization_id: UUID,
        types: Optional[list[str]] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> SearchResponse:
        """Execute hybrid search.

        Performance target: <100ms (p99)
        """
        start = time.monotonic()

        # Run vector and BM25 searches in parallel
        vector_task = self._vector_search(query, organization_id, types)
        bm25_task = self._bm25_search(query, organization_id, types)

        vector_results, bm25_results = await asyncio.gather(vector_task, bm25_task)

        # Reciprocal Rank Fusion
        fused = self._rrf_fusion(vector_results, bm25_results)

        # Apply pagination
        paginated = fused[offset : offset + limit]
        total = len(fused)

        # Hydrate with full data
        results = await self._hydrate(paginated, organization_id, query)

        elapsed = int((time.monotonic() - start) * 1000)

        return SearchResponse(
            results=results,
            total=total,
            took_ms=elapsed,
            query=query,
        )

    async def _vector_search(
        self,
        query: str,
        organization_id: UUID,
        types: Optional[list[str]],
    ) -> list[tuple[UUID, float]]:
        """Semantic search using pgvector HNSW index."""
        # Embed the query
        embedding = await self.embedding.embed([query])
        query_vector = embedding[0]

        # Convert embedding vector to pgvector literal string format
        query_vec_str = "[" + ",".join(str(v) for v in query_vector) + "]"
        params: list[Any] = [query_vec_str, organization_id]
        type_filter = ""
        if types:
            type_filter = f" AND node_type::text = ANY(${len(params) + 1}::text[])"
            params.append(types)

        rows = await self.db.fetch_all(
            f"""
            SELECT id, 1 - (embedding <=> $1::vector) AS score
            FROM nodes
            WHERE organization_id = $2
              AND deleted_at IS NULL
              AND embedding IS NOT NULL
              {type_filter}
            ORDER BY embedding <=> $1::vector
            LIMIT 20
            """,
            *params,
        )

        return [(r["id"], r["score"]) for r in rows]

    async def _bm25_search(
        self,
        query: str,
        organization_id: UUID,
        types: Optional[list[str]],
    ) -> list[tuple[UUID, float]]:
        """Full-text keyword search using PostgreSQL tsvector."""
        params: list[Any] = [query, organization_id]
        type_filter = ""
        if types:
            type_filter = f" AND node_type::text = ANY(${len(params) + 1}::text[])"
            params.append(types)

        rows = await self.db.fetch_all(
            f"""
            SELECT id, ts_rank(search_vector, plainto_tsquery('english', $1)) AS score
            FROM nodes
            WHERE organization_id = $2
              AND deleted_at IS NULL
              AND search_vector @@ plainto_tsquery('english', $1)
              {type_filter}
            ORDER BY score DESC
            LIMIT 20
            """,
            *params,
        )

        return [(r["id"], r["score"]) for r in rows]

    def _rrf_fusion(
        self,
        *result_lists: list[tuple[UUID, float]],
    ) -> list[UUID]:
        """Reciprocal Rank Fusion.

        RRF(d) = Σ 1/(k + rank_i(d))
        """
        scores: dict[UUID, float] = defaultdict(float)

        for results in result_lists:
            for rank, (doc_id, _) in enumerate(results, 1):
                scores[doc_id] += 1.0 / (self.rrf_k + rank)

        # Sort descending by fused score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return sorted_ids

    async def _hydrate(
        self,
        node_ids: list[UUID],
        organization_id: UUID,
        query: str = "",
    ) -> list[SearchResult]:
        """Fetch full row data for a list of node IDs, with optional highlighting."""
        if not node_ids:
            return []

        if query:
            rows = await self.db.fetch_all(
                """
                SELECT
                  id, node_type::text, title, description,
                  ts_headline('english', title,
                    plainto_tsquery('english', $3)) AS title_hl,
                  ts_headline('english', description,
                    plainto_tsquery('english', $3)) AS desc_hl
                FROM nodes
                WHERE id = ANY($1::uuid[])
                  AND organization_id = $2
                  AND deleted_at IS NULL
                """,
                node_ids,
                organization_id,
                query,
            )
        else:
            rows = await self.db.fetch_all(
                """
                SELECT id, node_type::text, title, description,
                       NULL AS title_hl, NULL AS desc_hl
                FROM nodes
                WHERE id = ANY($1::uuid[])
                  AND organization_id = $2
                  AND deleted_at IS NULL
                """,
                node_ids,
                organization_id,
            )

        # Build lookup
        lookup = {r["id"]: r for r in rows}

        results: list[SearchResult] = []
        for node_id in node_ids:
            row = lookup.get(node_id)
            if row:
                highlights = [h for h in [row.get("title_hl"), row.get("desc_hl")] if h]
                results.append(
                    SearchResult(
                        id=row["id"],
                        node_type=row["node_type"],
                        title=row["title"],
                        description=row["description"],
                        score=0.0,  # Score is from RRF, set by caller
                        highlights=highlights,
                    )
                )
        return results
