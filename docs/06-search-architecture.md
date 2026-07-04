# ResearchOS - Search Architecture

## Overview

ResearchOS provides a hybrid search system combining semantic (vector), keyword (BM25), and graph-based search to enable researchers to find experiments, papers, notebooks, and other research objects.

---

## Design Goals

1. **< 100ms Latency**: Sub-100ms search response time (p99)
2. **Hybrid Search**: Combine semantic + keyword + graph
3. **No External Search Engine**: Use PostgreSQL + pgvector only
4. **Real-Time Indexing**: Embeddings generated on write
5. **Multi-Tenant Isolation**: Organization-scoped search

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│  - Frontend search bar                                               │
│  - API /v1/search                                                    │
│  - AI RAG queries                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SEARCH SERVICE                                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Query Processor                                                │ │
│  │  - Tokenization                                                │ │
│  │  - Query expansion                                             │ │
│  │  - Filter parsing                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Hybrid Search                                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │ │
│  │  │   Vector     │  │    BM25      │  │    Graph     │        │ │
│  │  │   Search     │  │   Search     │  │   Search     │        │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Result Ranking                                                 │ │
│  │  - Reciprocal Rank Fusion (RRF)                                │ │
│  │  - Deduplication                                               │ │
│  │  - Personalization                                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     POSTGRESQL + PGVECTOR                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  nodes table                                                    │ │
│  │  - embedding vector(1536)                                      │ │
│  │  - search_vector tsvector                                      │ │
│  │  - title_trgm gin_trgm_ops                                     │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Indexes                                                        │ │
│  │  - HNSW for vector search                                      │ │
│  │  - GIN for full-text search                                    │ │
│  │  - GIN for trigram fuzzy search                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Search Types

### 1. Semantic Search (Vector)

```
Query: "failed due to memory error"
        │
        ▼
Embedding Model (text-embedding-3-small)
        │
        ▼
Vector: [0.123, -0.456, ...] (1536 dimensions)
        │
        ▼
Cosine Similarity Search (HNSW index)
        │
        ▼
Results:
  - experiment_123 (score: 0.92)
  - run_456 (score: 0.87)
  - paper_789 (score: 0.81)
```

**When to use**:
- Natural language queries
- Conceptual search
- Finding similar experiments

### 2. Keyword Search (BM25 + Trigram)

```
Query: "resnet accuracy"
        │
        ▼
Tokenization: ["resnet", "accuracy"]
        │
        ▼
Full-Text Search (tsvector)
        │
        ▼
Trigram Search (fuzzy matching)
        │
        ▼
Results:
  - experiment: ResNet-50 Training (score: 0.85)
  - paper: "Accuracy Analysis of ResNet" (score: 0.78)
  - notebook: "ResNet Experiments" (score: 0.72)
```

**When to use**:
- Exact term matching
- Code snippets
- Technical terms

### 3. Graph Search

```
Query: "experiments that test hypothesis X"
        │
        ▼
Parse: Find node type=experiment, edge_type=tests, target=hypothesis_X
        │
        ▼
Graph Traversal
        │
        ▼
Results:
  - experiment_123
  - experiment_456
```

**When to use**:
- Relationship queries
- Provenance queries
- Impact analysis

---

## Hybrid Search Pipeline

```
┌────────────────────────────────────────────────────────────────────┐
│  INPUT: query + filters + scope                                    │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  STEP 1: PARALLEL SEARCH                                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Vector Search                    BM25 Search                 │ │
│  │  - Embed query                    - Tokenize query           │ │
│  │  - Cosine similarity              - TF-IDF scoring           │ │
│  │  - Top-K=20                       - Top-K=20                 │ │
│  │                                                                   │ │
│  │  Results:                         Results:                    │ │
│  │  1. exp_123 (0.92)                1. exp_123 (8.5)          │ │
│  │  2. exp_456 (0.87)                2. paper_789 (7.2)        │ │
│  │  3. paper_789 (0.81)              3. nb_111 (6.8)           │ │
│  │  ...                              ...                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Graph Search (if relationship query)                         │ │
│  │  - Parse query                                                │ │
│  │  - Traverse edges                                             │ │
│  │  - Top-K=20                                                  │ │
│  │                                                                   │ │
│  │  Results:                                                     │ │
│  │  1. exp_123                                                   │ │
│  │  2. exp_456                                                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  STEP 2: FUSION (Reciprocal Rank Fusion)                           │
│                                                                    │
│  Formula: RRF(d) = Σ 1/(k + rank(d))                              │
│  where k=60 (constant)                                            │
│                                                                    │
│  exp_123:  1/(60+1) + 1/(60+1) + 1/(60+1) = 0.049               │
│  paper_789: 1/(60+3) + 1/(60+2) = 0.032                          │
│                                                                    │
│  Combined Results:                                                 │
│  1. exp_123 (0.049)                                               │
│  2. paper_789 (0.032)                                             │
│  3. exp_456 (0.028)                                               │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  STEP 3: RERANKING (optional)                                      │
│  - Cross-encoder reranking for top 20 results                     │
│  - Personalization based on user history                          │
│  - Freshness boost (recent items)                                 │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  STEP 4: DEDUPLICATION & FILTERING                                 │
│  - Remove duplicates                                              │
│  - Apply filters (type, date range, tags)                        │
│  - Organization isolation                                          │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  OUTPUT: Ranked results with snippets                              │
└────────────────────────────────────────────────────────────────────┘
```

---

## Implementation

### Search Service

```python
# src/application/search/service.py

from uuid import UUID
from typing import Optional, list
from pydantic import BaseModel
from enum import Enum

class NodeType(Enum):
    EXPERIMENT = "experiment"
    PAPER = "paper"
    NOTEBOOK = "notebook"
    ARTIFACT = "artifact"
    HYPOTHESIS = "hypothesis"

class SearchFilter(BaseModel):
    types: Optional[list[NodeType]] = None
    tags: Optional[list[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    created_by: Optional[UUID] = None

class SearchResult(BaseModel):
    id: UUID
    node_type: NodeType
    title: str
    description: Optional[str]
    score: float
    highlights: list[str]
    metadata: dict

class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    took_ms: int
    query: str

class SearchService:
    """
    Hybrid search service combining vector, BM25, and graph search.
    """
    
    def __init__(
        self,
        db,
        embedding_adapter,
        k_vector: int = 20,
        k_bm25: int = 20,
        rrf_k: int = 60,
    ):
        self.db = db
        self.embedding = embedding_adapter
        self.k_vector = k_vector
        self.k_bm25 = k_bm25
        self.rrf_k = rrf_k
    
    async def search(
        self,
        query: str,
        organization_id: UUID,
        filters: Optional[SearchFilter] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> SearchResponse:
        """
        Execute hybrid search.
        
        Performance target: <100ms (p99)
        """
        import time
        start = time.time()
        
        # 1. Vector search (parallel)
        vector_task = self._vector_search(query, organization_id, filters)
        
        # 2. BM25 search (parallel)
        bm25_task = self._bm25_search(query, organization_id, filters)
        
        # 3. Graph search (if relationship query) (parallel)
        graph_results = await self._graph_search(query, organization_id, filters)
        
        # Wait for parallel tasks
        vector_results, bm25_results = await asyncio.gather(
            vector_task, bm25_task
        )
        
        # 4. Reciprocal Rank Fusion
        fused = self._rrf_fusion(vector_results, bm25_results, graph_results)
        
        # 5. Apply pagination
        paginated = fused[offset:offset + limit]
        
        # 6. Fetch full results
        results = await self._hydrate_results(paginated)
        
        took_ms = int((time.time() - start) * 1000)
        
        return SearchResponse(
            results=results,
            total=len(fused),
            took_ms=took_ms,
            query=query
        )
    
    async def _vector_search(
        self,
        query: str,
        organization_id: UUID,
        filters: Optional[SearchFilter],
    ) -> list[tuple[UUID, float]]:
        """Semantic search using pgvector HNSW index"""
        
        # Embed query
        embedding = await self.embedding.embed([query])
        query_vector = embedding[0]
        
        # Build filter clauses
        filter_clauses = self._build_filter_clauses(filters)
        
        # Execute vector search
        results = await self.db.fetch_all(
            f"""
            SELECT id, 1 - (embedding <=> $1::vector) as score
            FROM nodes
            WHERE organization_id = $2
            AND deleted_at IS NULL
            {filter_clauses}
            ORDER BY embedding <=> $1::vector
            LIMIT $3
            """,
            query_vector,
            organization_id,
            self.k_vector
        )
        
        return [(r["id"], r["score"]) for r in results]
    
    async def _bm25_search(
        self,
        query: str,
        organization_id: UUID,
        filters: Optional[SearchFilter],
    ) -> list[tuple[UUID, float]]:
        """Full-text search using PostgreSQL tsvector"""
        
        filter_clauses = self._build_filter_clauses(filters)
        
        results = await self.db.fetch_all(
            f"""
            SELECT id, ts_rank(search_vector, plainto_tsquery('english', $1)) as score
            FROM nodes
            WHERE organization_id = $2
            AND deleted_at IS NULL
            AND search_vector @@ plainto_tsquery('english', $1)
            {filter_clauses}
            ORDER BY ts_rank(search_vector, plainto_tsquery('english', $1)) DESC
            LIMIT $3
            """,
            query,
            organization_id,
            self.k_bm25
        )
        
        return [(r["id"], r["score"]) for r in results]
    
    async def _graph_search(
        self,
        query: str,
        organization_id: UUID,
        filters: Optional[SearchFilter],
    ) -> list[tuple[UUID, float]]:
        """Graph traversal search for relationship queries"""
        
        # Parse relationship query pattern
        # e.g., "experiments that test hypothesis X"
        parsed = self._parse_relationship_query(query)
        
        if not parsed:
            return []
        
        # Execute graph traversal
        results = await self.db.fetch_all(
            """
            WITH RECURSIVE related AS (
                SELECT source_id, target_id, edge_type, 1 as depth
                FROM edges
                WHERE deleted_at IS NULL
                AND organization_id = $1
                AND edge_type = $2
                
                UNION ALL
                
                SELECT e.source_id, e.target_id, e.edge_type, r.depth + 1
                FROM edges e
                JOIN related r ON e.source_id = r.target_id
                WHERE e.deleted_at IS NULL
                AND e.organization_id = $1
                AND r.depth < 3
            )
            SELECT DISTINCT source_id as id, 1.0 / depth as score
            FROM related
            WHERE target_id = $3
            LIMIT 20
            """,
            organization_id,
            parsed.get("edge_type"),
            parsed.get("target_id")
        )
        
        return [(r["id"], r["score"]) for r in results]
    
    def _rrf_fusion(
        self,
        vector_results: list[tuple[UUID, float]],
        bm25_results: list[tuple[UUID, float]],
        graph_results: list[tuple[UUID, float]],
    ) -> list[tuple[UUID, float]]:
        """
        Reciprocal Rank Fusion for combining search results.
        
        RRF(d) = Σ 1/(k + rank_i(d))
        """
        from collections import defaultdict
        
        scores = defaultdict(float)
        
        # Vector results
        for rank, (doc_id, _) in enumerate(vector_results, 1):
            scores[doc_id] += 1.0 / (self.rrf_k + rank)
        
        # BM25 results
        for rank, (doc_id, _) in enumerate(bm25_results, 1):
            scores[doc_id] += 1.0 / (self.rrf_k + rank)
        
        # Graph results
        for rank, (doc_id, _) in enumerate(graph_results, 1):
            scores[doc_id] += 1.0 / (self.rrf_k + rank)
        
        # Sort by combined score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_results
```

### API Endpoint

```python
# src/api/routes/search.py

from fastapi import APIRouter, Depends, Query
from uuid import UUID

router = APIRouter()

@router.get("/search")
async def search(
    q: str = Query(min_length=1, max_length=500),
    types: Optional[list[str]] = Query(None),
    tags: Optional[list[str]] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    organization_id: UUID = Depends(get_current_org),
    search_service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    """
    Hybrid search across research objects.
    
    Performance: <100ms (p99)
    """
    
    filters = SearchFilter(
        types=[NodeType(t) for t in types] if types else None,
        tags=tags,
        date_from=date_from,
        date_to=date_to,
    )
    
    return await search_service.search(
        query=q,
        organization_id=organization_id,
        filters=filters,
        limit=limit,
        offset=offset,
    )

@router.get("/search/suggestions")
async def suggestions(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=5, ge=1, le=10),
    organization_id: UUID = Depends(get_current_org),
    db = Depends(get_db),
) -> list[str]:
    """
    Autocomplete suggestions for search.
    """
    
    results = await db.fetch_all(
        """
        SELECT DISTINCT title
        FROM nodes
        WHERE organization_id = $1
        AND deleted_at IS NULL
        AND title % $2  -- Trigram similarity
        ORDER BY similarity(title, $2) DESC
        LIMIT $3
        """,
        organization_id,
        q,
        limit
    )
    
    return [r["title"] for r in results]
```

---

## Indexing Strategy

### Vector Index (HNSW)

```sql
-- HNSW index for fast approximate nearest neighbor search
CREATE INDEX idx_nodes_embedding ON nodes 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Parameters:
-- m = 16: Number of bi-directional links (higher = better recall, more memory)
-- ef_construction = 64: Size of dynamic candidate list during construction

-- Query-time parameter (per session)
SET hnsw.ef_search = 100;  -- Higher = better recall, slower
```

**Performance**:
- Build time: O(n log n)
- Query time: O(log n)
- Recall: 95%+ with ef_search=100

### Full-Text Index (GIN)

```sql
-- GIN index for tsvector
CREATE INDEX idx_nodes_search ON nodes USING GIN(search_vector);

-- Generated column for automatic tsvector update
ALTER TABLE nodes
ADD COLUMN search_vector tsvector GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(description, '')), 'B')
) STORED;
```

### Trigram Index (GIN)

```sql
-- Enable pg_trgm extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- GIN index for fuzzy matching
CREATE INDEX idx_nodes_title_trgm ON nodes USING gin(title gin_trgm_ops);

-- Usage for fuzzy search
SELECT * FROM nodes WHERE title % 'resnet' ORDER BY similarity(title, 'resnet') DESC;
```

---

## Embedding Generation

### Automatic Embedding on Write

```python
# src/infrastructure/workers/embedding_worker.py

class EmbeddingWorker:
    """
    Background worker that generates embeddings for nodes.
    
    Triggered by:
    - node.created event
    - node.updated event
    """
    
    async def on_node_created(self, event: NodeCreated):
        # Generate text for embedding
        node = await self.node_repo.get(event.node_id)
        text = f"{node.title}\n{node.description or ''}\n{json.dumps(node.properties)}"
        
        # Embed
        embedding = await self.embedding.embed([text])
        
        # Update node
        await self.db.execute(
            "UPDATE nodes SET embedding = $1 WHERE id = $2",
            embedding[0],
            node.id
        )
```

### Batch Embedding for Existing Data

```python
# scripts/batch_embed.py

async def batch_embed(organization_id: UUID):
    """
    Generate embeddings for nodes without embeddings.
    Run as one-time migration or scheduled job.
    """
    
    # Fetch nodes without embeddings
    nodes = await db.fetch_all(
        """
        SELECT id, title, description, properties
        FROM nodes
        WHERE organization_id = $1
        AND embedding IS NULL
        AND deleted_at IS NULL
        LIMIT 100
        """,
        organization_id
    )
    
    # Batch embed
    texts = [f"{n['title']}\n{n['description'] or ''}" for n in nodes]
    embeddings = await embedding.embed(texts)
    
    # Update
    for node, emb in zip(nodes, embeddings):
        await db.execute(
            "UPDATE nodes SET embedding = $1 WHERE id = $2",
            emb,
            node['id']
        )
```

---

## Performance Optimization

### Query Optimization

```sql
-- Combine vector and BM25 in single query
WITH vector_results AS (
    SELECT id, 1 - (embedding <=> $1::vector) as score
    FROM nodes
    WHERE organization_id = $2
    ORDER BY embedding <=> $1::vector
    LIMIT 20
),
bm25_results AS (
    SELECT id, ts_rank(search_vector, plainto_tsquery('english', $3)) as score
    FROM nodes
    WHERE organization_id = $2
    AND search_vector @@ plainto_tsquery('english', $3)
    ORDER BY score DESC
    LIMIT 20
)
SELECT 
    COALESCE(v.id, b.id) as id,
    COALESCE(v.score, 0) + COALESCE(b.score, 0) as combined_score
FROM vector_results v
FULL OUTER JOIN bm25_results b ON v.id = b.id
ORDER BY combined_score DESC
LIMIT 10;
```

### Caching

```python
# Cache popular queries
@cache.memoize(timeout=60)
async def search_cached(query_hash: str, org_id: UUID) -> SearchResponse:
    return await search_service.search(query, org_id)
```

### Connection Pooling

```python
# Use async connection pool
pool = await asyncpg.create_pool(
    database="researchos",
    min_size=10,
    max_size=50,
    command_timeout=5.0
)
```

---

## Search Features

### Faceted Search

```python
@router.get("/search/facets")
async def search_facets(
    q: str,
    organization_id: UUID = Depends(get_current_org),
) -> dict:
    """
    Get facet counts for search results.
    """
    
    return await db.fetch_one(
        """
        SELECT 
            json_object_agg(node_type, cnt) as types,
            json_object_agg(tag, tag_cnt) as tags
        FROM (
            SELECT node_type, COUNT(*) as cnt
            FROM nodes
            WHERE organization_id = $1
            AND search_vector @@ plainto_tsquery('english', $2)
            GROUP BY node_type
        ) t,
        (
            SELECT unnest(tags) as tag, COUNT(*) as tag_cnt
            FROM experiments
            WHERE organization_id = $1
            GROUP BY tag
        ) tg
        """,
        organization_id,
        q
    )
```

### Search Highlighting

```python
async def _hydrate_results(
    self,
    results: list[tuple[UUID, float]]
) -> list[SearchResult]:
    """Fetch full results with highlights"""
    
    ids = [r[0] for r in results]
    scores = dict(results)
    
    rows = await self.db.fetch_all(
        """
        SELECT 
            id, node_type, title, description,
            ts_headline('english', title, plainto_tsquery('english', $2)) as title_highlight,
            ts_headline('english', description, plainto_tsquery('english', $2)) as desc_highlight
        FROM nodes
        WHERE id = ANY($1)
        """,
        ids,
        self.query
    )
    
    return [
        SearchResult(
            id=r["id"],
            node_type=NodeType(r["node_type"]),
            title=r["title"],
            description=r["description"],
            score=scores[r["id"]],
            highlights=[
                r["title_highlight"],
                r["desc_highlight"]
            ].filter(None),
            metadata={}
        )
        for r in rows
    ]
```

---

## Monitoring

```python
# Track search performance
metrics.histogram("search.latency", took_ms, tags={
    "has_filters": filters is not None,
    "result_count": len(results)
})

# Track query patterns
metrics.increment("search.query", tags={
    "query_type": "hybrid"
})
```

---

## Next Steps

- AI architecture (RAG) → [05-ai-architecture.md](./05-ai-architecture.md)
- Research graph → [07-research-graph.md](./07-research-graph.md)
