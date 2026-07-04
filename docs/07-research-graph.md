# ResearchOS - Research Graph Design

## Overview

The Research Graph is the core data structure of ResearchOS. It models all research objects as nodes in a property graph with typed edges representing relationships like "derives_from", "tests", "generates", and more.

---

## Design Goals

1. **Graph-Centric**: Every research object is a node
2. **Typed Edges**: Semantic relationships between objects
3. **Version History**: Git-like DAG for versioning
4. **Forking**: Copy with lineage tracking
5. **Branching**: Parallel exploration
6. **Traversal**: Efficient graph queries

---

## Graph Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        RESEARCH GRAPH                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────┐         ┌────────────┐         ┌─────────────┐            │
│  │  Idea   │───────►│ Hypothesis │───────►│ Experiment  │            │
│  └─────────┘ derives_from          tests   └─────────────┘            │
│       │                                                │                  │
│       │                                                │                  │
│       │                                                ▼                  │
│       │                                       ┌─────────────┐            │
│       │                                       │    Run      │            │
│       │                                       └─────────────┘            │
│       │                                             │                  │
│       │                                             │                  │
│       │                                             ▼                  │
│       │                                       ┌─────────────┐            │
│       │                                       │   Metric    │            │
│       │                                       └─────────────┘            │
│       │                                                                  │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────┐             ┌─────────┐             ┌─────────────┐        │
│  │ Paper   │◄───────────│ Citation│◄───────────│  Artifact    │        │
│  └─────────┘ uses       └─────────┘ references  └─────────────┘        │
│       │                                                                  │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────┐                                                            │
│  │Notebook │                                                             │
│  └─────────┘                                                            │
│       │                                                                  │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────┐                                                            │
│  │ Block   │                                                             │
│  └─────────┘                                                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Node Types

| Node Type | Description | Key Properties |
|-----------|-------------|----------------|
| **Idea** | Initial research idea | title, description, tags |
| **Hypothesis** | Testable hypothesis | title, prediction, variables |
| **Experiment** | Experiment definition | name, parameters, status |
| **Run** | Single execution | run_number, git_commit, status |
| **Metric** | Measurement | key, value, step, timestamp |
| **Paper** | Research paper | title, abstract, doi |
| **Citation** | Bibliographic entry | authors, year, venue |
| **Dataset** | Data collection | name, size, format |
| **Model** | ML model | name, architecture, size |
| **Notebook** | Block-based notebook | title, branch, version |
| **Block** | Notebook block | block_type, position, content |
| **Artifact** | File artifact | name, type, size, hash |
| **Code** | Code snippet | language, content |
| **Insight** | Research insight | title, description, evidence |
| **Question** | Research question | title, priority, status |
| **Answer** | Answer to question | content, confidence |
| **Task** | Research task | title, assignee, status |

---

## Edge Types

| Edge Type | Source → Target | Meaning | Inverse |
|-----------|-----------------|---------|---------|
| `derives_from` | Hypothesis → Idea | Hypothesis comes from idea | - |
| `tests` | Experiment → Hypothesis | Experiment tests hypothesis | - |
| `supports` | Run → Hypothesis | Results support hypothesis | `contradicts` |
| `contradicts` | Run → Hypothesis | Results contradict hypothesis | `supports` |
| `contains` | Notebook → Block | Block is in notebook | `belongs_to` |
| `generates` | Run → Artifact | Run produced artifact | - |
| `uses` | Experiment → Dataset | Experiment uses dataset | - |
| `references` | Paper → Citation | Paper cites work | - |
| `cites` | Paper → Paper | Paper cites another paper | - |
| `authored_by` | Paper → Person | Author of paper | - |
| `based_on` | Experiment → Experiment | Derived from previous experiment | - |
| `extends` | Paper → Paper | Extension of previous paper | - |
| `replaces` | Version → Version | New version replaces old | - |
| `version_of` | Node → Node | Version relationship | - |
| `fork_of` | Node → Node | Forked from original | - |
| `merged_from` | Node → Node | Merged from branch | - |

---

## Version History

### Git-Like DAG Structure

```
                    ┌─────────────────────────────────────┐
                    │      VERSION HISTORY (DAG)          │
                    └─────────────────────────────────────┘
                                     
                    Time ─────────────────────────────────►
                    
                    v1          v2          v3          v4
                    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐
                    │ A   │───►│ B   │───►│ C   │───►│ D   │  main
                    └─────┘    └─────┘    └─────┘    └─────┘
                         │                  │
                         │                  │
                         ▼                  ▼
                    ┌─────┐              ┌─────┐
                    │ E   │              │ F   │───►│ G   │  feature-x
                    └─────┘              └─────┘    └─────┘
                         │                  │
                         │                  │
                         └──────────┬───────┘
                                    │
                                    ▼
                              ┌─────┐
                              │ H   │  merged
                              └─────┘
                              
                    # Node H merges feature-x into main
                    # Edges: merged_from → E, merged_from → G
```

### Implementation

```python
# src/domain/graph/entities.py

class Node(BaseModel):
    id: UUID
    organization_id: UUID
    node_type: NodeType
    title: str
    properties: dict
    
    # Version control
    version: int = 1
    parent_version_id: Optional[UUID] = None  # Previous version
    
    # Branching
    branch: str = "main"
    
    # Forking
    is_fork: bool = False
    forked_from_id: Optional[UUID] = None  # Original node
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    created_by: UUID
```

---

## Branching

### Branch Model

```
┌────────────────────────────────────────────────────────────────────┐
│                      BRANCH STRUCTURE                              │
└────────────────────────────────────────────────────────────────────┘

main                ┌────────┐────►┌────────┐────►┌────────┐
(created)            │ v1     │     │ v2     │     │ v3     │
                    └────────┘     └────────┘     └────────┘
                         │
                         │ branch created
                         ▼
feature-optimize     ┌────────┐────►┌────────┐
                    │ v1     │     │ v2     │
                    └────────┘     └────────┘
                         │
                         │ commit
                         ▼
                    ┌────────┐
                    │ v3     │
                    └────────┘
                         │
                         │ merge
                         ▼
main                ┌────────┐────►┌────────┐────►┌────────┐
                    │ v1     │     │ v2     │     │ v4     │  (merged)
                    └────────┘     └────────┘     └────────┘
                                                     ▲
                                                     │
                                                     │ merged_from = feature-optimize v3
```

### Branch Entity

```python
class Branch(BaseModel):
    id: UUID
    organization_id: UUID
    name: str  # e.g., "main", "feature-x"
    parent_branch: Optional[str] = None  # "main"
    head_commit: Optional[str] = None  # SHA of latest commit
    
    # Merge status
    is_merged: bool = False
    merged_at: Optional[datetime] = None
    merged_into: Optional[str] = None  # Target branch name
    
    created_at: datetime
    created_by: UUID
```

### Operations

```python
# src/application/graph/branch_service.py

class BranchService:
    async def create_branch(
        self,
        entity_type: str,  # "notebook", "experiment", "paper"
        entity_id: UUID,
        branch_name: str,
        from_branch: str = "main",
        created_by: UUID,
    ) -> Branch:
        """Create a new branch from an existing branch"""
        
        # Check branch doesn't exist
        existing = await self.branch_repo.get(entity_type, entity_id, branch_name)
        if existing:
            raise ValueError(f"Branch {branch_name} already exists")
        
        # Get head of source branch
        head_commit = await self.commit_repo.get_head(entity_type, entity_id, from_branch)
        
        branch = Branch(
            organization_id=org_id,
            entity_type=entity_type,
            entity_id=entity_id,
            name=branch_name,
            parent_branch=from_branch,
            head_commit=head_commit.sha if head_commit else None,
            created_by=created_by
        )
        
        await self.branch_repo.save(branch)
        return branch
    
    async def merge_branch(
        self,
        entity_type: str,
        entity_id: UUID,
        source_branch: str,
        target_branch: str = "main",
        merged_by: UUID,
    ) -> Node:
        """Merge source branch into target branch"""
        
        # Get heads of both branches
        source_head = await self.commit_repo.get_head(entity_type, entity_id, source_branch)
        target_head = await self.commit_repo.get_head(entity_type, entity_id, target_branch)
        
        # Create merge commit
        merge_commit = Commit(
            organization_id=org_id,
            entity_type=entity_type,
            entity_id=entity_id,
            branch=target_branch,
            parent_sha=target_head.sha if target_head else None,
            message=f"Merge {source_branch}",
            created_by=merged_by
        )
        
        # Create merged_from edge
        await self.edge_repo.create(Edge(
            source_id=merge_commit.id,
            target_id=source_head.node_id,
            edge_type=EdgeType.MERGED_FROM
        ))
        
        # Update branch status
        await self.branch_repo.update(source_branch, is_merged=True, merged_at=now())
        
        return merge_commit
```

---

## Forking

### Fork Model

```
┌────────────────────────────────────────────────────────────────┐
│                      FORK STRUCTURE                            │
└────────────────────────────────────────────────────────────────┘

Original (Organization A)
┌────────┐────►┌────────┐────►┌────────┐
│ v1     │     │ v2     │     │ v3     │  main
└────────┘     └────────┘     └────────┘
     │
     │ fork
     ▼
Fork (Organization B)
┌────────┐────►┌────────┐
│ v1     │     │ v2'    │  main (independently versioned)
└────────┘     └────────┘
     ▲
     │
     │ fork_of edge
     │
Original v1

# Fork tracks lineage via fork_of edge
# Each fork has independent version history
```

### Fork Entity

```python
class Fork(BaseModel):
    id: UUID
    organization_id: UUID
    source_node_id: UUID  # Original node
    source_branch: str  # Branch that was forked
    target_branch: str  # New branch name
    created_at: datetime
    created_by: UUID
```

### Operations

```python
# src/application/graph/fork_service.py

class ForkService:
    async def fork_node(
        self,
        node_id: UUID,
        target_organization_id: UUID,
        target_branch: str = "main",
        created_by: UUID,
    ) -> Node:
        """Fork a node to a different organization"""
        
        # Get original node
        original = await self.node_repo.get(node_id)
        
        # Create fork
        fork = Node(
            organization_id=target_organization_id,
            node_type=original.node_type,
            title=f"Fork: {original.title}",
            properties=original.properties.copy(),
            version=1,  # Reset version
            branch=target_branch,
            is_fork=True,
            forked_from_id=original.id,
            created_by=created_by
        )
        
        await self.node_repo.save(fork)
        
        # Create fork_of edge
        await self.edge_repo.create(Edge(
            organization_id=target_organization_id,
            source_id=fork.id,
            target_id=original.id,
            edge_type=EdgeType.FORK_OF
        ))
        
        return fork
```

---

## Graph Traversal

### Common Queries

```python
# src/application/graph/traversal.py

class GraphService:
    async def get_ancestors(
        self,
        node_id: UUID,
        edge_types: Optional[list[EdgeType]] = None,
        max_depth: int = 10,
    ) -> list[Node]:
        """
        Find all ancestors (upstream) of a node.
        
        Example: Find all experiments that led to this one.
        """
        
        edge_types = edge_types or [
            EdgeType.DERIVES_FROM,
            EdgeType.BASES_ON,
            EdgeType.VERSION_OF
        ]
        
        results = await self.db.fetch_all(
            """
            WITH RECURSIVE ancestors AS (
                -- Base: direct ancestors
                SELECT source_id, target_id, edge_type, 1 as depth
                FROM edges
                WHERE target_id = $1
                AND deleted_at IS NULL
                AND edge_type = ANY($2)
                
                UNION ALL
                
                -- Recursive: ancestors of ancestors
                SELECT e.source_id, e.target_id, e.edge_type, a.depth + 1
                FROM edges e
                JOIN ancestors a ON e.target_id = a.source_id
                WHERE e.deleted_at IS NULL
                AND e.edge_type = ANY($2)
                AND a.depth < $3
            )
            SELECT DISTINCT source_id
            FROM ancestors
            ORDER BY depth
            """,
            node_id,
            [e.value for e in edge_types],
            max_depth
        )
        
        return await self.node_repo.get_many([r["source_id"] for r in results])
    
    async def get_descendants(
        self,
        node_id: UUID,
        edge_types: Optional[list[EdgeType]] = None,
        max_depth: int = 10,
    ) -> list[Node]:
        """
        Find all descendants (downstream) of a node.
        
        Example: Find all experiments that test this hypothesis.
        """
        
        edge_types = edge_types or [
            EdgeType.DERIVES_FROM,
            EdgeType.TESTS,
            EdgeType.GENERATES
        ]
        
        results = await self.db.fetch_all(
            """
            WITH RECURSIVE descendants AS (
                -- Base: direct descendants
                SELECT source_id, target_id, edge_type, 1 as depth
                FROM edges
                WHERE source_id = $1
                AND deleted_at IS NULL
                AND edge_type = ANY($2)
                
                UNION ALL
                
                -- Recursive: descendants of descendants
                SELECT e.source_id, e.target_id, e.edge_type, d.depth + 1
                FROM edges e
                JOIN descendants d ON e.source_id = d.target_id
                WHERE e.deleted_at IS NULL
                AND e.edge_type = ANY($2)
                AND d.depth < $3
            )
            SELECT DISTINCT target_id
            FROM descendants
            ORDER BY depth
            """,
            node_id,
            [e.value for e in edge_types],
            max_depth
        )
        
        return await self.node_repo.get_many([r["target_id"] for r in results])
    
    async def find_path(
        self,
        source_id: UUID,
        target_id: UUID,
        max_depth: int = 5,
    ) -> Optional[list[Node]]:
        """
        Find shortest path between two nodes.
        
        Example: How is experiment A related to paper B?
        """
        
        results = await self.db.fetch_all(
            """
            WITH RECURSIVE path AS (
                -- Base
                SELECT 
                    source_id,
                    target_id,
                    ARRAY[source_id] as visited,
                    1 as depth
                FROM edges
                WHERE source_id = $1
                AND deleted_at IS NULL
                
                UNION ALL
                
                -- Recursive
                SELECT
                    e.source_id,
                    e.target_id,
                    p.visited || e.target_id,
                    p.depth + 1
                FROM edges e
                JOIN path p ON e.source_id = p.target_id
                WHERE e.deleted_at IS NULL
                AND e.target_id != ALL(p.visited)
                AND p.depth < $3
            )
            SELECT visited
            FROM path
            WHERE target_id = $2
            ORDER BY depth
            LIMIT 1
            """,
            source_id,
            target_id,
            max_depth
        )
        
        if not results:
            return None
        
        node_ids = results[0]["visited"]
        return await self.node_repo.get_many(node_ids)
    
    async def get_neighbors(
        self,
        node_id: UUID,
        edge_types: Optional[list[EdgeType]] = None,
        direction: str = "both",  # "incoming", "outgoing", "both"
    ) -> dict[EdgeType, list[Node]]:
        """
        Get immediate neighbors of a node.
        
        Returns: Dict of edge_type -> list of nodes
        """
        
        direction_clause = {
            "incoming": "target_id = $1",
            "outgoing": "source_id = $1",
            "both": "(source_id = $1 OR target_id = $1)"
        }[direction]
        
        filter_clause = ""
        if edge_types:
            filter_clause = "AND edge_type = ANY($2)"
        
        results = await self.db.fetch_all(
            f"""
            SELECT 
                edge_type,
                CASE 
                    WHEN source_id = $1 THEN target_id
                    ELSE source_id
                END as neighbor_id
            FROM edges
            WHERE {direction_clause}
            AND deleted_at IS NULL
            {filter_clause}
            """,
            node_id,
            [e.value for e in edge_types] if edge_types else None
        )
        
        # Group by edge type
        neighbors = defaultdict(list)
        for r in results:
            edge_type = EdgeType(r["edge_type"])
            node = await self.node_repo.get(r["neighbor_id"])
            if node:
                neighbors[edge_type].append(node)
        
        return dict(neighbors)
```

---

## Timeline & Evolution

### Timeline Query

```python
async def get_timeline(
    self,
    organization_id: UUID,
    entity_type: Optional[NodeType] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 100,
) -> list[tuple[datetime, Node, list[Edge]]]:
    """
    Get timeline of research activities.
    
    Returns: List of (timestamp, node, edges) tuples
    """
    
    results = await self.db.fetch_all(
        """
        SELECT 
            n.id,
            n.node_type,
            n.title,
            n.created_at,
            n.updated_at,
            COALESCE(
                json_agg(
                    json_build_object(
                        'id', e.id,
                        'type', e.edge_type,
                        'target', e.target_id
                    )
                ) FILTER (WHERE e.id IS NOT NULL),
                '[]'::json
            ) as edges
        FROM nodes n
        LEFT JOIN edges e ON n.id = e.source_id AND e.deleted_at IS NULL
        WHERE n.organization_id = $1
        AND n.deleted_at IS NULL
        AND ($2::node_type IS NULL OR n.node_type = $2)
        AND ($3::timestamptz IS NULL OR n.created_at >= $3)
        AND ($4::timestamptz IS NULL OR n.created_at <= $4)
        GROUP BY n.id
        ORDER BY n.created_at DESC
        LIMIT $5
        """,
        organization_id,
        entity_type.value if entity_type else None,
        from_date,
        to_date,
        limit
    )
    
    return results
```

### Evolution Tree

```python
async def get_evolution_tree(
    self,
    node_id: UUID,
) -> dict:
    """
    Get version tree for a node.
    
    Returns: Tree structure with versions and branches.
    """
    
    results = await self.db.fetch_all(
        """
        WITH RECURSIVE versions AS (
            -- Base: all versions of this node
            SELECT id, version, parent_version_id, branch, created_at
            FROM nodes
            WHERE id = $1 OR forked_from_id = $1
            AND deleted_at IS NULL
            
            UNION ALL
            
            -- Recursive: parent versions
            SELECT n.id, n.version, n.parent_version_id, n.branch, n.created_at
            FROM nodes n
            JOIN versions v ON n.id = v.parent_version_id
            WHERE n.deleted_at IS NULL
        )
        SELECT 
            v.id,
            v.version,
            v.parent_version_id,
            v.branch,
            v.created_at,
            EXISTS(SELECT 1 FROM nodes WHERE parent_version_id = v.id) as has_children
        FROM versions v
        ORDER BY v.created_at
        """,
        node_id
    )
    
    # Build tree structure
    tree = {"root": node_id, "nodes": {}, "branches": {}}
    
    for r in results:
        tree["nodes"][r["id"]] = {
            "version": r["version"],
            "parent": r["parent_version_id"],
            "branch": r["branch"],
            "created_at": r["created_at"],
            "children": []
        }
        
        if r["branch"] not in tree["branches"]:
            tree["branches"][r["branch"]] = []
        tree["branches"][r["branch"]].append(r["id"])
    
    # Link children
    for r in results:
        if r["parent_version_id"]:
            tree["nodes"][r["parent_version_id"]]["children"].append(r["id"])
    
    return tree
```

---

## Impact Analysis

```python
async def get_impact(
    self,
    node_id: UUID,
) -> dict:
    """
    Get impact of a node (how many downstream objects depend on it).
    """
    
    results = await self.db.fetch_one(
        """
        WITH RECURSUS impact AS (
            SELECT source_id, target_id, 1 as depth
            FROM edges
            WHERE source_id = $1
            AND deleted_at IS NULL
            
            UNION ALL
            
            SELECT e.source_id, e.target_id, i.depth + 1
            FROM edges e
            JOIN impact i ON e.source_id = i.target_id
            WHERE e.deleted_at IS NULL
            AND i.depth < 10
        )
        SELECT 
            COUNT(DISTINCT target_id) as total_impact,
            COUNT(DISTINCT target_id) FILTER (WHERE depth = 1) as direct_impact,
            MAX(depth) as max_depth
        FROM impact
        """,
        node_id
    )
    
    return {
        "total_impact": results["total_impact"],
        "direct_impact": results["direct_impact"],
        "max_depth": results["max_depth"]
    }
```

---

## API Endpoints

```python
# src/api/routes/graph.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/graph/nodes/{node_id}")
async def get_node(node_id: UUID) -> Node:
    """Get node by ID"""
    return await graph_service.get_node(node_id)

@router.get("/graph/nodes/{node_id}/edges")
async def get_edges(
    node_id: UUID,
    direction: str = "both",
    edge_types: Optional[list[str]] = Query(None)
) -> dict:
    """Get edges for a node"""
    return await graph_service.get_neighbors(
        node_id,
        [EdgeType(t) for t in edge_types] if edge_types else None,
        direction
    )

@router.get("/graph/nodes/{node_id}/ancestors")
async def get_ancestors(
    node_id: UUID,
    max_depth: int = 10
) -> list[Node]:
    """Get ancestor nodes"""
    return await graph_service.get_ancestors(node_id, max_depth=max_depth)

@router.get("/graph/nodes/{node_id}/descendants")
async def get_descendants(
    node_id: UUID,
    max_depth: int = 10
) -> list[Node]:
    """Get descendant nodes"""
    return await graph_service.get_descendants(node_id, max_depth=max_depth)

@router.get("/graph/traverse")
async def traverse(
    start: UUID,
    end: Optional[UUID] = None,
    edge_types: Optional[list[str]] = Query(None),
    max_depth: int = 5
) -> list[Node]:
    """Traverse graph from start node"""
    if end:
        path = await graph_service.find_path(start, end, max_depth)
        return path or []
    return await graph_service.get_descendants(
        start,
        [EdgeType(t) for t in edge_types] if edge_types else None,
        max_depth
    )

@router.get("/graph/timeline")
async def timeline(
    entity_type: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 100,
    organization_id: UUID = Depends(get_current_org)
) -> list[dict]:
    """Get timeline of research activities"""
    return await graph_service.get_timeline(
        organization_id,
        NodeType(entity_type) if entity_type else None,
        from_date,
        to_date,
        limit
    )

@router.get("/graph/nodes/{node_id}/evolution")
async def evolution(node_id: UUID) -> dict:
    """Get evolution tree for a node"""
    return await graph_service.get_evolution_tree(node_id)

@router.get("/graph/nodes/{node_id}/impact")
async def impact(node_id: UUID) -> dict:
    """Get impact analysis for a node"""
    return await graph_service.get_impact(node_id)
```

---

## Visualization

### Force-Directed Layout

```typescript
// frontend/components/graph/GraphView.tsx

import { ForceGraph2D } from 'react-force-graph';

function GraphView({ nodes, edges }) {
  const graphData = {
    nodes: nodes.map(n => ({
      id: n.id,
      type: n.node_type,
      label: n.title
    })),
    links: edges.map(e => ({
      source: e.source_id,
      target: e.target_id,
      type: e.edge_type
    }))
  };
  
  return (
    <ForceGraph2D
      graphData={graphData}
      nodeColor={node => nodeColors[node.type]}
      nodeLabel={node => node.label}
      linkDirectionalArrowLength={5}
      onNodeClick={node => navigate(`/nodes/${node.id}`)}
    />
  );
}
```

### Tree Layout

```typescript
// frontend/components/graph/EvolutionTree.tsx

function EvolutionTree({ tree }) {
  return (
    <Tree
      data={buildTree(tree)}
      orientation="vertical"
      pathFunc="elbow"
      nodeSize={{ x: 150, y: 50 }}
      renderNode={node => (
        <NodeCard node={node} />
      )}
    />
  );
}
```

---

## Next Steps

- Notebook architecture → [08-notebook-architecture.md](./08-notebook-architecture.md)
- Search architecture → [06-search-architecture.md](./06-search-architecture.md)
