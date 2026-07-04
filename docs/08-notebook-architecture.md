# ResearchOS - Notebook Architecture

## Overview

ResearchOS notebooks are block-based documents for research composition. Unlike Jupyter, they feature:
- Independent block versioning
- Git-like branching and merging
- Reusable blocks
- Multi-language execution (Python, Rust, SQL, Mermaid, etc.)

---

## Design Goals

1. **NOT Jupyter**: Different execution model, storage, versioning
2. **Block-Level Versioning**: Not full notebook snapshots
3. **Reusable Blocks**: Reference blocks across notebooks
4. **Git-Compatible**: Stored as versioned files
5. **Multi-Language**: Support Python, Rust, SQL, Mermaid, LaTeX, etc.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                                │
│  - Block-based editor (TipTap)                                       │
│  - Code execution panel                                              │
│  - Version history timeline                                          │
│  - Branch switcher                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     NOTEBOOK SERVICE                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Block Management                                               │ │
│  │  - Add/remove/reorder blocks                                   │ │
│  │  - Block versioning                                            │ │
│  │  - Block references (reusable blocks)                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Execution Engine                                               │ │
│  │  - Kernel management (Python, Rust)                            │ │
│  │  - Cell execution                                               │ │
│  │  - Output capture                                               │ │
│  │  - State isolation                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Version Control                                                │ │
│  │  - Branch creation/merge                                       │ │
│  │  - Version history                                             │ │
│  │  - Diff view                                                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL                                                     │ │
│  │  - notebooks (metadata)                                        │ │
│  │  - blocks (identity, position)                                │ │
│  │  - block_contents (immutable versions)                         │ │
│  │  - executions (run history)                                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Object Storage (S3/MinIO)                                     │ │
│  │  - Notebook files (.ipynb export)                              │ │
│  │  - Execution outputs (images, data)                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     EXECUTION LAYER                                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Kernel Pool                                                    │ │
│  │  - Python kernels (ipykernel)                                  │ │
│  │  - Rust kernels (evcxr)                                        │ │
│  │  - SQL engines (PostgreSQL, DuckDB)                            │ │
│  │  - Mermaid renderer                                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Model

### Core Entities

```python
# src/domain/notebooks/entities.py

from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import Optional

class BlockType(str, Enum):
    MARKDOWN = "markdown"
    PYTHON = "python"
    RUST = "rust"
    SQL = "sql"
    MERMAID = "mermaid"
    LATEX = "latex"
    DIAGRAM = "diagram"
    EXPERIMENT_CARD = "experiment_card"  # Embed experiment
    METRIC = "metric"                    # Display metric
    CITATION = "citation"                # Citation block
    AI_SUMMARY = "ai_summary"            # AI-generated summary

class Notebook(BaseModel):
    """
    Notebook aggregate root.
    
    Contains metadata and block references.
    Content is managed at block level.
    """
    
    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    project_id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    
    # Version control
    branch: str = "main"
    parent_commit: Optional[str] = None  # SHA
    
    # Block references (ordered)
    block_ids: list[UUID] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID

class Block(BaseModel):
    """
    Block entity.
    
    Has identity and position.
    Content is stored separately in BlockContent.
    """
    
    id: UUID = Field(default_factory=uuid4)
    notebook_id: UUID
    organization_id: UUID
    block_type: BlockType
    position: int = Field(ge=0)
    
    # Current content version
    current_version: int = 1
    
    # Execution settings (for code blocks)
    auto_execute: bool = False
    timeout_ms: int = 30000
    
    # Reusable block reference
    reference_block_id: Optional[UUID] = None  # If this is a reference
    
    # Timestamps
    created_at: datetime
    updated_at: datetime

class BlockContent(BaseModel):
    """
    BlockContent entity (immutable).
    
    Each version of a block's content is a new record.
    Enables:
    - Version history
    - Diff view
    - Rewind
    """
    
    id: UUID = Field(default_factory=uuid4)
    block_id: UUID
    organization_id: UUID
    version: int = Field(ge=1)
    
    # Content
    content: str
    
    # For code blocks
    language: Optional[str] = None
    
    # Metadata
    metadata: dict = Field(default_factory=dict)
    
    # Audit
    created_at: datetime
    created_by: UUID

class Execution(BaseModel):
    """
    Execution entity.
    
    Records the result of executing a block.
    """
    
    id: UUID = Field(default_factory=uuid4)
    block_content_id: UUID
    notebook_id: UUID
    organization_id: UUID
    
    # Status
    status: ExecutionStatus
    
    # Timing
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    # Output
    output: Optional[str] = None  # Text output
    error: Optional[str] = None  # Error message
    
    # Generated artifacts
    artifact_ids: list[UUID] = Field(default_factory=list)
    
    # Audit
    created_by: UUID

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
```

---

## Block Types

### Markdown Block

```python
{
    "block_type": "markdown",
    "content": """
# Introduction

This notebook demonstrates...

## Methods

- Item 1
- Item 2
"""
}
```

### Python Block

```python
{
    "block_type": "python",
    "language": "python",
    "content": """
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data.csv')
df.head()
""",
    "auto_execute": False,
    "timeout_ms": 30000
}
```

### Rust Block

```python
{
    "block_type": "rust",
    "language": "rust",
    "content": """
use ndarray::Array2;

let a = Array2::<f64>::zeros((3, 3));
println!("{:?}", a);
"""
}
```

### SQL Block

```python
{
    "block_type": "sql",
    "language": "sql",
    "content": """
SELECT 
    experiment_id,
    AVG(accuracy) as avg_accuracy,
    COUNT(*) as run_count
FROM experiments e
JOIN runs r ON e.id = r.experiment_id
JOIN metrics m ON r.id = m.run_id
WHERE m.key = 'accuracy'
GROUP BY experiment_id
ORDER BY avg_accuracy DESC
LIMIT 10;
"""
}
```

### Mermaid Block

```python
{
    "block_type": "mermaid",
    "language": "mermaid",
    "content": """
graph TD
    A[Load Data] --> B[Preprocess]
    B --> C[Train Model]
    C --> D{Evaluate}
    D -->|Good| E[Deploy]
    D -->|Bad| F[Tune]
    F --> C
"""
}
```

### LaTeX Block

```python
{
    "block_type": "latex",
    "language": "latex",
    "content": r"""
\begin{equation}
\mathcal{L} = -\frac{1}{N} \sum_{i=1}^{N} y_i \log(\hat{y}_i) + (1-y_i) \log(1-\hat{y}_i)
\end{equation}
"""
}
```

### Experiment Card Block

```python
{
    "block_type": "experiment_card",
    "content": "",
    "metadata": {
        "experiment_id": "exp_123",
        "display": "summary"  # "summary", "metrics", "comparison"
    }
}
```

Rendered as:
```
┌──────────────────────────────────────┐
│ Experiment: ResNet-50 Training       │
│ Status: completed                     │
│ Runs: 12 | Best Accuracy: 94.2%      │
│ [View Details] [Compare]             │
└──────────────────────────────────────┘
```

### Metric Block

```python
{
    "block_type": "metric",
    "content": "",
    "metadata": {
        "experiment_id": "exp_123",
        "metric_key": "accuracy",
        "chart_type": "line"  # "line", "bar", "scatter"
    }
}
```

Renders an interactive chart.

### Citation Block

```python
{
    "block_type": "citation",
    "content": "",
    "metadata": {
        "citation_key": "vaswani2017attention",
        "format": "APA"  # "APA", "MLA", "Chicago", "BibTeX"
    }
}
```

Renders:
> Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & Polosukhin, I. (2017). Attention is all you need. *Advances in neural information processing systems*, 30.

### AI Summary Block

```python
{
    "block_type": "ai_summary",
    "content": "This experiment achieved 94.2% accuracy...",
    "metadata": {
        "generated_by": "gpt-4o",
        "generated_at": "2024-01-15T10:30:00Z",
        "context": ["exp_123", "exp_456"]
    }
}
```

---

## Block-Content Separation

### Why Separate?

1. **Independent Versioning**: Each block evolves independently
2. **Efficient Diffs**: Only changed blocks need new versions
3. **Reusable Blocks**: Reference same content across notebooks
4. **Fast Operations**: Reorder doesn't touch content

### Example

```
Notebook A (main branch)
┌─────────────────────────────────────────────────────────────┐
│ Block 1 (markdown) │ v1 │ "Introduction..."                │
├─────────────────────────────────────────────────────────────┤
│ Block 2 (python)   │ v3 │ "import pandas as pd..."        │
├─────────────────────────────────────────────────────────────┤
│ Block 3 (markdown) │ v1 │ "## Results..."                  │
└─────────────────────────────────────────────────────────────┘

Notebook A (edit block 2)
┌─────────────────────────────────────────────────────────────┐
│ Block 1 (markdown) │ v1 │ "Introduction..."               │  (unchanged)
├─────────────────────────────────────────────────────────────┤
│ Block 2 (python)   │ v4 │ "import numpy as np..."         │  NEW VERSION
├─────────────────────────────────────────────────────────────┤
│ Block 3 (markdown) │ v1 │ "## Results..."                 │  (unchanged)
└─────────────────────────────────────────────────────────────┘
```

---

## Execution Engine

### Kernel Management

```python
# src/infrastructure/notebooks/kernel_pool.py

import asyncio
from typing import Optional
from uuid import UUID
import jupyter_client

class KernelManager:
    """
    Manages IPython kernels for notebook execution.
    
    Features:
    - Kernel pooling
    - State isolation
    - Timeout handling
    - Output capture
    """
    
    def __init__(self, max_kernels: int = 10):
        self.max_kernels = max_kernels
        self.kernels: dict[UUID, jupyter_client.KernelClient] = {}
        self.lock = asyncio.Lock()
    
    async def get_kernel(self, notebook_id: UUID) -> jupyter_client.KernelClient:
        """Get or create kernel for notebook"""
        
        async with self.lock:
            if notebook_id in self.kernels:
                return self.kernels[notebook_id]
            
            if len(self.kernels) >= self.max_kernels:
                # Evict oldest kernel
                oldest = next(iter(self.kernels))
                await self.kill_kernel(oldest)
            
            # Create new kernel
            kernel_manager = jupyter_client.KernelManager(kernel_name='python3')
            await kernel_manager.start_kernel()
            
            client = kernel_manager.client()
            client.start_channels()
            await client.wait_for_ready()
            
            self.kernels[notebook_id] = client
            return client
    
    async def execute(
        self,
        notebook_id: UUID,
        code: str,
        timeout_ms: int = 30000,
    ) -> ExecutionResult:
        """Execute code in kernel"""
        
        kernel = await self.get_kernel(notebook_id)
        
        # Execute
        msg_id = kernel.execute(code)
        
        # Collect output
        outputs = []
        errors = []
        
        try:
            async with asyncio.timeout(timeout_ms / 1000):
                while True:
                    msg = kernel.get_iopub_msg(timeout=1)
                    
                    if msg['header']['msg_type'] == 'stream':
                        outputs.append(msg['content']['text'])
                    elif msg['header']['msg_type'] == 'error':
                        errors.append(msg['content']['traceback'])
                    elif msg['header']['msg_type'] == 'status':
                        if msg['content']['execution_state'] == 'idle':
                            break
        except asyncio.TimeoutError:
            # Force interrupt
            kernel.interrupt_kernel()
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                output="".join(outputs),
                error="Execution timed out"
            )
        
        if errors:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                output="".join(outputs),
                error="\n".join(errors[-1])
            )
        
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            output="".join(outputs)
        )
    
    async def kill_kernel(self, notebook_id: UUID) -> None:
        """Kill kernel for notebook"""
        if notebook_id in self.kernels:
            kernel = self.kernels.pop(notebook_id)
            kernel.stop_channels()
            # Kill kernel process
```

### SQL Execution

```python
# src/infrastructure/notebooks/sql_executor.py

class SQLExecutor:
    """Execute SQL queries against database"""
    
    def __init__(self, db_pool):
        self.db = db_pool
    
    async def execute(
        self,
        sql: str,
        organization_id: UUID,
        timeout_ms: int = 30000,
    ) -> ExecutionResult:
        """Execute SQL query"""
        
        try:
            async with asyncio.timeout(timeout_ms / 1000):
                results = await self.db.fetch_all(sql)
                
                # Format as table
                output = self._format_results(results)
                
                return ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    output=output
                )
        
        except asyncio.TimeoutError:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                error="Query timed out"
            )
        
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                error=str(e)
            )
```

### Mermaid Rendering

```python
# src/infrastructure/notebooks/mermaid_renderer.py

import subprocess

class MermaidRenderer:
    """Render Mermaid diagrams to SVG/PNG"""
    
    async def render(self, mermaid_code: str, format: str = "svg") -> str:
        """Render Mermaid diagram"""
        
        # Use mmdc CLI (Mermaid CLI)
        result = subprocess.run(
            ["mmdc", "-i", "-", "-o", "-", "-f", format],
            input=mermaid_code,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise ValueError(result.stderr)
        
        return result.stdout
```

---

## Version Control

### Branch Operations

```python
# src/application/notebooks/branch_service.py

class NotebookBranchService:
    async def create_branch(
        self,
        notebook_id: UUID,
        branch_name: str,
        from_branch: str = "main",
        created_by: UUID,
    ) -> Notebook:
        """Create a new branch"""
        
        # Get current notebook state
        notebook = await self.notebook_repo.get(notebook_id)
        
        # Copy blocks to new branch
        new_notebook = Notebook(
            id=uuid4(),
            organization_id=notebook.organization_id,
            project_id=notebook.project_id,
            title=notebook.title,
            branch=branch_name,
            parent_commit=None,
            block_ids=notebook.block_ids.copy(),
            created_by=created_by
        )
        
        await self.notebook_repo.save(new_notebook)
        
        # Create branch record
        branch = Branch(
            organization_id=notebook.organization_id,
            entity_type="notebook",
            entity_id=notebook_id,
            name=branch_name,
            parent_branch=from_branch,
            created_by=created_by
        )
        
        await self.branch_repo.save(branch)
        
        return new_notebook
    
    async def merge_branch(
        self,
        notebook_id: UUID,
        source_branch: str,
        target_branch: str = "main",
        merged_by: UUID,
    ) -> Notebook:
        """Merge source branch into target branch"""
        
        # Get both versions
        source = await self.notebook_repo.get_by_branch(notebook_id, source_branch)
        target = await self.notebook_repo.get_by_branch(notebook_id, target_branch)
        
        # Detect conflicts
        conflicts = await self._detect_conflicts(source, target)
        
        if conflicts:
            raise MergeConflictError(conflicts)
        
        # Merge
        merged = self._merge_notebooks(source, target)
        
        await self.notebook_repo.save(merged)
        await self.branch_repo.mark_merged(source_branch)
        
        return merged
    
    async def _detect_conflicts(
        self,
        source: Notebook,
        target: Notebook,
    ) -> list[Conflict]:
        """Detect merge conflicts"""
        
        conflicts = []
        
        # Check for blocks modified in both branches
        for block_id in source.block_ids:
            if block_id in target.block_ids:
                source_content = await self.block_repo.get_content(block_id, source.branch)
                target_content = await self.block_repo.get_content(block_id, target.branch)
                
                if source_content.version != target_content.version:
                    # Check if they diverged from same base
                    if source_content.parent_version == target_content.parent_version:
                        conflicts.append(Conflict(
                            block_id=block_id,
                            source_version=source_content.version,
                            target_version=target_content.version
                        ))
        
        return conflicts
```

### Version History

```python
# src/application/notebooks/version_service.py

class NotebookVersionService:
    async def get_history(
        self,
        notebook_id: UUID,
        branch: str = "main",
        limit: int = 50,
    ) -> list[VersionInfo]:
        """Get version history for notebook"""
        
        # Get all block versions in chronological order
        history = await self.db.fetch_all(
            """
            SELECT 
                bc.id as content_id,
                bc.block_id,
                bc.version,
                bc.created_at,
                bc.created_by,
                b.block_type,
                u.name as author_name
            FROM block_contents bc
            JOIN blocks b ON bc.block_id = b.id
            JOIN notebooks n ON b.notebook_id = n.id
            JOIN users u ON bc.created_by = u.id
            WHERE n.id = $1
            AND n.branch = $2
            ORDER BY bc.created_at DESC
            LIMIT $3
            """,
            notebook_id,
            branch,
            limit
        )
        
        return history
    
    async def get_diff(
        self,
        notebook_id: UUID,
        version1: int,
        version2: int,
    ) -> DiffResult:
        """Get diff between two versions"""
        
        # Get block contents for both versions
        v1_contents = await self._get_version_contents(notebook_id, version1)
        v2_contents = await self._get_version_contents(notebook_id, version2)
        
        # Compute diff
        diff = difflib.unified_diff(
            v1_contents.splitlines(),
            v2_contents.splitlines(),
            lineterm=''
        )
        
        return DiffResult(
            version1=version1,
            version2=version2,
            diff=''.join(diff)
        )
    
    async def restore_version(
        self,
        notebook_id: UUID,
        version: int,
        restored_by: UUID,
    ) -> Notebook:
        """Restore notebook to a previous version"""
        
        # Get version state
        version_state = await self._get_version_state(notebook_id, version)
        
        # Create new version with restored state
        for block_id, content in version_state.items():
            new_content = BlockContent(
                block_id=block_id,
                version=await self._get_next_version(block_id),
                content=content,
                created_by=restored_by
            )
            await self.block_content_repo.save(new_content)
        
        return await self.notebook_repo.get(notebook_id)
```

---

## Reusable Blocks

### Block References

```python
# src/application/notebooks/reference_service.py

class BlockReferenceService:
    """
    Manage block references across notebooks.
    
    A reference is a block that points to another block's content.
    Changes to the original are reflected in all references.
    """
    
    async def create_reference(
        self,
        source_block_id: UUID,
        target_notebook_id: UUID,
        position: int,
        created_by: UUID,
    ) -> Block:
        """Create a reference to an existing block"""
        
        # Get source block
        source = await self.block_repo.get(source_block_id)
        
        # Create reference block
        reference = Block(
            notebook_id=target_notebook_id,
            organization_id=source.organization_id,
            block_type=source.block_type,
            position=position,
            reference_block_id=source_block_id,  # Points to source
            created_by=created_by
        )
        
        await self.block_repo.save(reference)
        
        return reference
    
    async def resolve_reference(self, block: Block) -> BlockContent:
        """Get content for a reference block"""
        
        if not block.reference_block_id:
            raise ValueError("Block is not a reference")
        
        # Get source block's current content
        source_content = await self.block_content_repo.get_latest(
            block.reference_block_id
        )
        
        return source_content
    
    async def update_source(
        self,
        block_id: UUID,
        new_content: str,
        updated_by: UUID,
    ) -> list[Block]:
        """
        Update source block and notify all references.
        
        Returns: List of affected reference blocks
        """
        
        # Create new version
        content = BlockContent(
            block_id=block_id,
            version=await self._get_next_version(block_id),
            content=new_content,
            created_by=updated_by
        )
        
        await self.block_content_repo.save(content)
        
        # Find all references
        references = await self.block_repo.find_references(block_id)
        
        return references
```

---

## API Endpoints

```python
# src/api/routes/notebooks.py

from fastapi import APIRouter

router = APIRouter()

@router.post("/notebooks")
async def create_notebook(
    title: str,
    project_id: UUID,
    organization_id: UUID = Depends(get_current_org),
    user_id: UUID = Depends(get_current_user),
) -> Notebook:
    """Create a new notebook"""
    return await notebook_service.create(title, project_id, organization_id, user_id)

@router.get("/notebooks/{notebook_id}")
async def get_notebook(
    notebook_id: UUID,
    branch: str = "main",
) -> NotebookResponse:
    """Get notebook with blocks"""
    return await notebook_service.get_with_blocks(notebook_id, branch)

@router.patch("/notebooks/{notebook_id}/blocks")
async def update_blocks(
    notebook_id: UUID,
    operations: list[BlockOperation],
    user_id: UUID = Depends(get_current_user),
) -> Notebook:
    """Update notebook blocks"""
    return await notebook_service.apply_operations(notebook_id, operations, user_id)

@router.post("/notebooks/{notebook_id}/blocks/{block_id}/execute")
async def execute_block(
    notebook_id: UUID,
    block_id: UUID,
    timeout_ms: int = 30000,
    user_id: UUID = Depends(get_current_user),
) -> Execution:
    """Execute a block"""
    return await execution_service.execute_block(
        notebook_id, block_id, timeout_ms, user_id
    )

@router.post("/notebooks/{notebook_id}/execute")
async def execute_notebook(
    notebook_id: UUID,
    user_id: UUID = Depends(get_current_user),
) -> list[Execution]:
    """Execute all blocks in notebook"""
    return await execution_service.execute_notebook(notebook_id, user_id)

@router.post("/notebooks/{notebook_id}/branches")
async def create_branch(
    notebook_id: UUID,
    branch_name: str,
    from_branch: str = "main",
    user_id: UUID = Depends(get_current_user),
) -> Notebook:
    """Create a new branch"""
    return await branch_service.create_branch(
        notebook_id, branch_name, from_branch, user_id
    )

@router.post("/notebooks/{notebook_id}/merge")
async def merge_branch(
    notebook_id: UUID,
    source_branch: str,
    target_branch: str = "main",
    user_id: UUID = Depends(get_current_user),
) -> Notebook:
    """Merge branches"""
    return await branch_service.merge_branch(
        notebook_id, source_branch, target_branch, user_id
    )

@router.get("/notebooks/{notebook_id}/history")
async def get_history(
    notebook_id: UUID,
    branch: str = "main",
    limit: int = 50,
) -> list[VersionInfo]:
    """Get version history"""
    return await version_service.get_history(notebook_id, branch, limit)

@router.get("/notebooks/{notebook_id}/diff")
async def get_diff(
    notebook_id: UUID,
    v1: int,
    v2: int,
) -> DiffResult:
    """Get diff between versions"""
    return await version_service.get_diff(notebook_id, v1, v2)
```

---

## Export

### Jupyter Notebook Export

```python
# src/application/notebooks/export.py

class NotebookExporter:
    async def export_jupyter(self, notebook_id: UUID) -> dict:
        """Export to Jupyter notebook format (.ipynb)"""
        
        notebook = await self.notebook_repo.get(notebook_id)
        blocks = await self.block_repo.get_by_notebook(notebook_id)
        
        cells = []
        for block in blocks:
            content = await self.block_content_repo.get_latest(block.id)
            
            if block.block_type == BlockType.MARKDOWN:
                cells.append({
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": content.content.split('\n')
                })
            elif block.block_type in [BlockType.PYTHON, BlockType.RUST]:
                cells.append({
                    "cell_type": "code",
                    "metadata": {},
                    "source": content.content.split('\n'),
                    "outputs": [],
                    "execution_count": None
                })
        
        return {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "cells": cells
        }
```

### PDF Export

```python
async def export_pdf(self, notebook_id: UUID) -> bytes:
    """Export to PDF"""
    
    # Export to LaTeX first
    latex = await self.export_latex(notebook_id)
    
    # Use pandoc to convert
    result = subprocess.run(
        ["pandoc", "-f", "latex", "-t", "pdf", "-o", "-"],
        input=latex.encode(),
        capture_output=True
    )
    
    return result.stdout
```

---

## Frontend Components

### TipTap Editor

```typescript
// frontend/components/notebook/NotebookEditor.tsx

import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import CodeBlock from './extensions/CodeBlock';
import MermaidBlock from './extensions/MermaidBlock';

export function NotebookEditor({ notebookId }: { notebookId: string }) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      CodeBlock.configure({
        languages: ['python', 'rust', 'sql'],
        onExecute: async (blockId: string, code: string) => {
          const result = await executeBlock(notebookId, blockId, code);
          return result;
        }
      }),
      MermaidBlock,
    ],
    content: '<p>Start writing...</p>',
  });

  return (
    <EditorContent editor={editor} className="prose max-w-none" />
  );
}
```

### Block Component

```typescript
// frontend/components/notebook/Block.tsx

interface BlockProps {
  block: Block;
  onEdit: (content: string) => void;
  onExecute: () => void;
  onDelete: () => void;
}

export function Block({ block, onEdit, onExecute, onDelete }: BlockProps) {
  switch (block.block_type) {
    case 'markdown':
      return <MarkdownBlock content={block.content} onChange={onEdit} />;
    case 'python':
      return (
        <CodeBlock
          language="python"
          content={block.content}
          output={block.execution?.output}
          onChange={onEdit}
          onExecute={onExecute}
        />
      );
    case 'mermaid':
      return <MermaidDiagram definition={block.content} />;
    case 'experiment_card':
      return <ExperimentCard experimentId={block.metadata.experiment_id} />;
    default:
      return <div>Unknown block type</div>;
  }
}
```

---

## Next Steps

- Event architecture → [09-event-architecture.md](./09-event-architecture.md)
- Research graph → [07-research-graph.md](./07-research-graph.md)
