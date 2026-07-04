# ResearchOS - AI Architecture

## Overview

ResearchOS features a multi-agent AI system that assists researchers with discovering insights, analyzing experiments, writing papers, and navigating the research graph.

---

## Design Goals

1. **Multi-Agent Orchestration**: Specialized agents for different tasks
2. **RAG (Retrieval-Augmented Generation)**: Ground answers in user data
3. **Tool Integration**: Agents can read/write research graph
4. **MCP Compatible**: Model Context Protocol for extensibility
5. **Prompt Management**: Versioned, A/B tested prompts

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                                 │
│  - /ask endpoint (REST)                                                 │
│  - AI Sidebar (Frontend)                                                │
│  - Inline assistance in notebooks                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        API LAYER (/v1/ask)                              │
│  - Request validation                                                   │
│  - Context resolution                                                   │
│  - Response streaming (SSE)                                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR (Application Service)                   │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Query Understanding                                                │ │
│  │  - Intent classification                                           │ │
│  │  - Entity extraction                                                │ │
│  │  - Context scoping                                                  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Agent Selection                                                    │ │
│  │  - Route to appropriate agent(s)                                   │ │
│  │  - Parallel or sequential execution                                │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Context Assembly                                                   │ │
│  │  - Retrieve relevant context (RAG)                                 │ │
│  │  - Inject into prompt                                              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          AGENT LAYER                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   Planner    │  │   Retriever  │  │  Research    │                  │
│  │   Agent      │  │   Agent      │  │  Analyst     │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Experiment   │  │    Paper     │  │    Code      │                  │
│  │  Analyst     │  │   Writer     │  │  Reviewer    │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │    Tool      │  │    Memory    │  │  Knowledge   │                  │
│  │  Executor    │  │   Manager    │  │    Graph     │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          TOOLS LAYER (MCP)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   Search     │  │   Graph      │  │  Notebook    │                  │
│  │   Tool       │  │  Traversal   │  │   Tool       │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  Experiment  │  │   Metric     │  │   Paper      │                  │
│  │   Tool       │  │   Tool       │  │   Tool       │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ LLM Adapters │  │  Embedding   │  │   Vector     │                  │
│  │(OpenAI, etc) │  │  Adapters    │  │   Store      │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│  ┌──────────────┐  ┌──────────────┐                                  │
│  │    Prompt    │  │   Content    │                                  │
│  │   Manager    │  │   Store      │                                  │
│  └──────────────┘  └──────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Types

### 1. Planner Agent

**Purpose**: Understand user intent and plan execution

**Responsibilities**:
- Query understanding and intent classification
- Task decomposition
- Agent routing
- Execution planning

**Example**:
```
User: "Why did experiment X fail?"
Planner:
1. Classify: experiment_analysis
2. Decompose: 
   - Find experiment X
   - Retrieve error logs
   - Analyze failure patterns
3. Route: ExperimentAnalyst
```

### 2. Retriever Agent

**Purpose**: Find relevant information in research graph

**Responsibilities**:
- Semantic search
- Graph traversal
- Context ranking
- Deduplication

**Output**: Ranked list of relevant contexts (experiments, papers, metrics)

### 3. Research Analyst Agent

**Purpose**: Answer questions about research methodology

**Responsibilities**:
- Explain research concepts
- Suggest hypotheses
- Compare approaches
- Identify patterns

**Example**:
```
User: "What's the best architecture for image classification?"
ResearchAnalyst:
1. Search for related experiments
2. Compare accuracy metrics
3. Analyze trends
4. Generate recommendation
```

### 4. Experiment Analyst Agent

**Purpose**: Analyze and debug experiments

**Responsibilities**:
- Interpret metrics
- Identify anomalies
- Debug failures
- Suggest improvements

**Tools**:
- `get_experiment`: Fetch experiment details
- `get_metrics`: Retrieve metric history
- `compare_runs`: Compare multiple runs
- `find_similar`: Find similar experiments

### 5. Paper Writer Agent

**Purpose**: Assist with paper composition

**Responsibilities**:
- Generate sections
- Format citations
- Suggest structure
- Maintain consistency

**Tools**:
- `get_paper`: Fetch paper state
- `update_section`: Edit sections
- `add_citation`: Add references
- `format_bibliography`: Format citations

### 6. Code Reviewer Agent

**Purpose**: Review code in notebooks

**Responsibilities**:
- Identify issues
- Suggest improvements
- Explain code behavior
- Check correctness

### 7. Tool Executor Agent

**Purpose**: Execute tools on behalf of other agents

**Responsibilities**:
- Tool invocation
- Result formatting
- Error handling
- Rate limiting

### 8. Memory Agent

**Purpose**: Maintain conversation memory

**Responsibilities**:
- Track conversation history
- Extract entities
- Maintain context
- Summarize long conversations

### 9. Knowledge Graph Agent

**Purpose**: Navigate and query the research graph

**Responsibilities**:
- Graph traversal
- Path finding
- Node ranking
- Relationship queries

---

## Tool Definitions (MCP)

```python
# src/infrastructure/ai/tools.py

from mcp import Tool, Parameter
from pydantic import BaseModel

class SearchTool(Tool):
    """Semantic search across research graph"""
    
    name = "search"
    description = "Search for experiments, papers, notebooks, or metrics"
    
    parameters = [
        Parameter("query", type="string", description="Search query"),
        Parameter("filters", type="object", description="Optional filters"),
        Parameter("limit", type="integer", default=10, description="Max results"),
    ]
    
    async def execute(self, query: str, filters: dict = None, limit: int = 10):
        # Call search service
        results = await self.search_service.search(
            query=query,
            filters=filters,
            limit=limit
        )
        return results

class GetExperimentTool(Tool):
    """Fetch experiment details"""
    
    name = "get_experiment"
    description = "Get experiment by ID or name"
    
    parameters = [
        Parameter("experiment_id", type="string", description="Experiment ID or name"),
    ]
    
    async def execute(self, experiment_id: str):
        experiment = await self.experiment_repo.get(experiment_id)
        return experiment.model_dump()

class GetMetricsTool(Tool):
    """Retrieve metric history"""
    
    name = "get_metrics"
    description = "Get metrics for a run or experiment"
    
    parameters = [
        Parameter("run_id", type="string", description="Run ID"),
        Parameter("keys", type="array", description="Metric keys to fetch"),
    ]
    
    async def execute(self, run_id: str, keys: list[str] = None):
        metrics = await self.metric_repo.get_by_run(run_id, keys)
        return {"metrics": metrics}

class CompareRunsTool(Tool):
    """Compare multiple runs"""
    
    name = "compare_runs"
    description = "Compare metrics across runs"
    
    parameters = [
        Parameter("run_ids", type="array", description="Run IDs to compare"),
        Parameter("metrics", type="array", description="Metrics to compare"),
    ]
    
    async def execute(self, run_ids: list[str], metrics: list[str]):
        comparison = await self.analysis_service.compare_runs(run_ids, metrics)
        return comparison

class GraphTraversalTool(Tool):
    """Traverse research graph"""
    
    name = "graph_traverse"
    description = "Find related nodes in the research graph"
    
    parameters = [
        Parameter("start_node", type="string", description="Starting node ID"),
        Parameter("edge_types", type="array", description="Edge types to follow"),
        Parameter("max_depth", type="integer", default=3),
    ]
    
    async def execute(self, start_node: str, edge_types: list[str], max_depth: int = 3):
        nodes = await self.graph_service.traverse(
            start_node=start_node,
            edge_types=edge_types,
            max_depth=max_depth
        )
        return {"nodes": nodes}

class UpdateNotebookTool(Tool):
    """Update notebook block"""
    
    name = "update_notebook"
    description = "Add or update blocks in a notebook"
    
    parameters = [
        Parameter("notebook_id", type="string"),
        Parameter("operation", type="string", enum=["add", "update", "delete"]),
        Parameter("block", type="object"),
    ]
    
    async def execute(self, notebook_id: str, operation: str, block: dict):
        result = await self.notebook_service.update_block(
            notebook_id, operation, block
        )
        return result
```

---

## RAG Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                         QUERY FLOW                                   │
└─────────────────────────────────────────────────────────────────────┘

User Query: "Why did experiment X fail?"
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  1. QUERY UNDERSTANDING                                             │
│     - Intent: experiment_analysis                                   │
│     - Entities: experiment_id=X                                     │
│     - Context scope: experiment, runs, metrics, logs                │
└─────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. RETRIEVAL                                                       │
│     ┌───────────────────────────────────────────────────────────┐  │
│     │ A. Semantic Search                                        │  │
│     │    Query: "experiment failure error logs X"              │  │
│     │    Index: nodes (experiments, runs)                       │  │
│     │    Top-K: 10                                             │  │
│     └───────────────────────────────────────────────────────────┘  │
│     ┌───────────────────────────────────────────────────────────┐  │
│     │ B. Graph Traversal                                        │  │
│     │    Start: node X                                          │  │
│     │    Follow: generates, contains                            │  │
│     │    Retrieve: runs, metrics, artifacts                     │  │
│     └───────────────────────────────────────────────────────────┘  │
│     ┌───────────────────────────────────────────────────────────┐  │
│     │ C. Keyword Search                                         │  │
│     │    Query: "error", "failed", "exception"                  │  │
│     │    Scope: logs, output                                    │  │
│     └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3. CONTEXT ASSEMBLY                                                │
│     - Merge results from all sources                                │
│     - Deduplicate                                                   │
│     - Rank by relevance                                             │
│     - Truncate to token budget                                      │
└─────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  4. PROMPT CONSTRUCTION                                             │
│     ┌───────────────────────────────────────────────────────────┐  │
│     │ System Prompt (base)                                      │  │
│     │                                                           │  │
│     │ You are an experiment analyst. Help users debug           │  │
│     │ failed experiments using the provided context.             │  │
│     └───────────────────────────────────────────────────────────┘  │
│     ┌───────────────────────────────────────────────────────────┐  │
│     │ Context (retrieved data)                                  │  │
│     │                                                           │  │
│     │ Experiment: X                                            │  │
│     │ - Status: failed                                          │  │
│     │ - Last run: run_123                                       │  │
│     │ - Error: CUDA out of memory                               │  │
│     │ - Metrics before failure:                                 │  │
│     │   * gpu_memory_used: 15.8 GB                              │  │
│     │   * batch_size: 128                                       │  │
│     └───────────────────────────────────────────────────────────┘  │
│     ┌───────────────────────────────────────────────────────────┐  │
│     │ User Query                                                │  │
│     │                                                           │  │
│     │ Why did experiment X fail?                                │  │
│     └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  5. LLM GENERATION                                                  │
│     - Model: GPT-4o                                                 │
│     - Temperature: 0.7                                              │
│     - Max tokens: 1000                                              │
└─────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  6. RESPONSE                                                        │
│     Experiment X failed due to a CUDA out-of-memory error.          │
│     The GPU memory usage reached 15.8 GB, which exceeds the         │
│     available memory.                                               │
│                                                                     │
│     Recommendation: Reduce batch_size from 128 to 64 to halve       │
│     memory consumption.                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## LLM Adapters

```python
# src/infrastructure/ai/llm/__init__.py

from abc import ABC, abstractmethod
from typing import AsyncIterator
from pydantic import BaseModel

class LLMAdapter(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        pass
    
    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        pass

class OpenAIAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
    
    async def stream_generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

class AnthropicAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
    
    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

class OllamaAdapter(LLMAdapter):
    """Local LLM via Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model
    
    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False}
            )
            return response.json()["response"]
```

---

## Embedding Adapters

```python
# src/infrastructure/ai/embeddings/__init__.py

from abc import ABC, abstractmethod
import numpy as np

class EmbeddingAdapter(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts"""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension"""
        pass

class OpenAIEmbeddingAdapter(EmbeddingAdapter):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [e.embedding for e in response.data]
    
    @property
    def dimension(self) -> int:
        return 1536  # text-embedding-3-small

class CohereEmbeddingAdapter(EmbeddingAdapter):
    def __init__(self, api_key: str, model: str = "embed-english-v3.0"):
        import cohere
        self.client = cohere.AsyncClient(api_key)
        self.model = model
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embed(texts=texts, model=self.model)
        return response.embeddings
    
    @property
    def dimension(self) -> int:
        return 1024

class LocalEmbeddingAdapter(EmbeddingAdapter):
    """Local embedding model via sentence-transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
    
    @property
    def dimension(self) -> int:
        return 384
```

---

## Prompt Management

```python
# src/infrastructure/ai/prompts/__init__.py

from pydantic import BaseModel
from typing import Optional
import yaml
from pathlib import Path

class PromptTemplate(BaseModel):
    id: str
    version: str
    name: str
    description: str
    template: str
    variables: list[str]
    metadata: dict = {}

class PromptManager:
    """
    Manages prompt templates with versioning.
    
    Prompts stored in: backend/prompts/
    Format: YAML files
    
    Features:
    - Versioning
    - A/B testing support
    - Variable interpolation
    """
    
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self.cache: dict[str, PromptTemplate] = {}
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        for file in self.prompts_dir.glob("**/*.yaml"):
            with open(file) as f:
                data = yaml.safe_load(f)
                prompt = PromptTemplate(**data)
                key = f"{prompt.id}:{prompt.version}"
                self.cache[key] = prompt
    
    def get(self, prompt_id: str, version: Optional[str] = None) -> PromptTemplate:
        """Get prompt by ID and optional version"""
        if version:
            key = f"{prompt_id}:{version}"
            if key not in self.cache:
                raise ValueError(f"Prompt {key} not found")
            return self.cache[key]
        
        # Get latest version
        versions = [k.split(":")[1] for k in self.cache if k.startswith(f"{prompt_id}:")]
        if not versions:
            raise ValueError(f"Prompt {prompt_id} not found")
        
        latest = sorted(versions)[-1]  # Semantic versioning
        return self.cache[f"{prompt_id}:{latest}"]
    
    def render(self, prompt_id: str, variables: dict, version: Optional[str] = None) -> str:
        """Render prompt with variables"""
        prompt = self.get(prompt_id, version)
        
        # Validate all variables provided
        missing = set(prompt.variables) - set(variables.keys())
        if missing:
            raise ValueError(f"Missing variables: {missing}")
        
        # Interpolate
        rendered = prompt.template
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        
        return rendered

# Example prompt file: prompts/experiment_analysis/v1.yaml
"""
id: experiment_analysis
version: "1.0.0"
name: Experiment Analysis
description: Analyze failed experiments and suggest fixes
template: |
  You are an experiment analyst. Help users debug failed experiments.
  
  Context:
  {{context}}
  
  User question: {{query}}
  
  Provide a clear, actionable answer.

variables:
  - context
  - query
metadata:
  model: gpt-4o
  temperature: 0.7
  max_tokens: 1000
"""
```

---

## Context Assembly

```python
# src/application/ai/context.py

from typing import list
from pydantic import BaseModel

class ContextAssembler:
    """
    Assembles context for RAG from multiple sources.
    
    Strategies:
    - Semantic search
    - Graph traversal
    - Recent history
    - User preferences
    """
    
    def __init__(
        self,
        search_service,
        graph_service,
        max_tokens: int = 4000,
    ):
        self.search_service = search_service
        self.graph_service = graph_service
        self.max_tokens = max_tokens
    
    async def assemble(
        self,
        query: str,
        organization_id: UUID,
        experiment_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> str:
        """Assemble context from multiple sources"""
        
        contexts = []
        
        # 1. Semantic search
        search_results = await self.search_service.search(
            query=query,
            organization_id=organization_id,
            limit=5
        )
        contexts.extend([r.content for r in search_results])
        
        # 2. Graph traversal (if entity detected)
        if experiment_id:
            related = await self.graph_service.traverse(
                start_node=experiment_id,
                edge_types=["generates", "contains", "tests"],
                max_depth=2
            )
            contexts.extend([self._format_node(n) for n in related])
        
        # 3. Deduplicate and rank
        unique_contexts = self._deduplicate(contexts)
        ranked_contexts = self._rank(unique_contexts, query)
        
        # 4. Truncate to token budget
        final_context = self._truncate(ranked_contexts, self.max_tokens)
        
        return "\n\n---\n\n".join(final_context)
    
    def _format_node(self, node) -> str:
        """Format node for context"""
        return f"[{node.node_type}] {node.title}: {node.description}"
    
    def _deduplicate(self, contexts: list[str]) -> list[str]:
        """Remove near-duplicates"""
        # Use MinHash or simple text similarity
        unique = []
        for ctx in contexts:
            if not any(self._similar(ctx, u) for u in unique):
                unique.append(ctx)
        return unique
    
    def _rank(self, contexts: list[str], query: str) -> list[str]:
        """Rank by relevance to query"""
        # Could use cross-encoder for re-ranking
        return contexts
    
    def _truncate(self, contexts: list[str], max_tokens: int) -> list[str]:
        """Truncate to token budget"""
        result = []
        total = 0
        for ctx in contexts:
            tokens = len(ctx.split())  # Approximate
            if total + tokens > max_tokens:
                break
            result.append(ctx)
            total += tokens
        return result
```

---

## Orchestration

```python
# src/application/ai/orchestrator.py

from uuid import UUID
from typing import Optional, AsyncIterator
from enum import Enum

class QueryIntent(Enum):
    EXPERIMENT_ANALYSIS = "experiment_analysis"
    PAPER_WRITING = "paper_writing"
    RESEARCH_QUESTION = "research_question"
    CODE_REVIEW = "code_review"
    NAVIGATION = "navigation"
    GENERAL = "general"

class AIOrchestrator:
    """
    Orchestrates multi-agent workflow for AI queries.
    """
    
    def __init__(
        self,
        llm_adapter,
        embedding_adapter,
        prompt_manager,
        context_assembler,
        search_service,
        graph_service,
    ):
        self.llm = llm_adapter
        self.embedding = embedding_adapter
        self.prompts = prompt_manager
        self.context = context_assembler
        self.search = search_service
        self.graph = graph_service
    
    async def ask(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        experiment_id: Optional[UUID] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Process user query and generate response.
        
        Yields response chunks if stream=True.
        """
        
        # 1. Understand query
        intent = await self._classify_intent(query)
        entities = await self._extract_entities(query)
        
        # 2. Retrieve context
        ctx = await self.context.assemble(
            query=query,
            organization_id=organization_id,
            experiment_id=entities.get("experiment_id"),
            user_id=user_id
        )
        
        # 3. Select agent
        agent = self._select_agent(intent)
        
        # 4. Render prompt
        prompt = self.prompts.render(
            prompt_id=f"{intent.value}_v1",
            variables={"context": ctx, "query": query}
        )
        
        # 5. Generate response
        if stream:
            async for chunk in self.llm.stream_generate(prompt):
                yield chunk
        else:
            response = await self.llm.generate(prompt)
            yield response
    
    async def _classify_intent(self, query: str) -> QueryIntent:
        """Classify query intent"""
        # Simple keyword matching (could use LLM)
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["experiment", "failed", "metrics", "run"]):
            return QueryIntent.EXPERIMENT_ANALYSIS
        elif any(kw in query_lower for kw in ["paper", "write", "section", "cite"]):
            return QueryIntent.PAPER_WRITING
        elif any(kw in query_lower for kw in ["hypothesis", "research", "study"]):
            return QueryIntent.RESEARCH_QUESTION
        elif any(kw in query_lower for kw in ["code", "review", "fix", "error"]):
            return QueryIntent.CODE_REVIEW
        elif any(kw in query_lower for kw in ["find", "show", "navigate", "where"]):
            return QueryIntent.NAVIGATION
        
        return QueryIntent.GENERAL
    
    async def _extract_entities(self, query: str) -> dict:
        """Extract named entities from query"""
        # Could use NER model or LLM
        return {}
    
    def _select_agent(self, intent: QueryIntent):
        """Select agent based on intent"""
        # Return specialized agent
        return self
```

---

## API Endpoint

```python
# src/api/routes/ask.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from uuid import UUID

router = APIRouter()

class AskRequest(BaseModel):
    query: str
    experiment_id: Optional[UUID] = None
    stream: bool = True

class AskResponse(BaseModel):
    response: str

@router.post("/ask")
async def ask(
    request: AskRequest,
    organization_id: UUID = Depends(get_current_org),
    user_id: UUID = Depends(get_current_user),
    orchestrator: AIOrchestrator = Depends(get_orchestrator),
):
    """Process AI query"""
    
    if request.stream:
        async def generate():
            async for chunk in orchestrator.ask(
                query=request.query,
                organization_id=organization_id,
                user_id=user_id,
                experiment_id=request.experiment_id,
                stream=True
            ):
                yield f"data: {chunk}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    else:
        response = await orchestrator.ask(
            query=request.query,
            organization_id=organization_id,
            user_id=user_id,
            experiment_id=request.experiment_id,
            stream=False
        ).__anext__()
        
        return AskResponse(response=response)
```

---

## Embedding Worker

```python
# src/infrastructure/workers/embedding_worker.py

import asyncio
from uuid import UUID

class EmbeddingWorker:
    """
    Background worker that generates embeddings for nodes.
    
    Triggered by:
    - Node created event
    - Node updated event
    - Scheduled batch job
    """
    
    def __init__(self, embedding_adapter, node_repo, event_consumer):
        self.embedding = embedding_adapter
        self.node_repo = node_repo
        self.event_consumer = event_consumer
    
    async def start(self) -> None:
        """Listen for events and generate embeddings"""
        async for event in self.event_consumer.subscribe(["node.created", "node.updated"]):
            await self._process_event(event)
    
    async def _process_event(self, event) -> None:
        """Generate embedding for node"""
        node_id = event.aggregate_id
        
        # Get node
        node = await self.node_repo.get_by_id(node_id)
        
        # Create text for embedding
        text = f"{node.title}\n{node.description or ''}"
        
        # Generate embedding
        embedding = await self.embedding.embed([text])
        
        # Update node
        node.embedding = embedding[0]
        await self.node_repo.save(node)
```

---

## Configuration

```yaml
# config/ai.yaml

llm:
  default_provider: openai
  providers:
    openai:
      api_key: ${OPENAI_API_KEY}
      model: gpt-4o
      temperature: 0.7
      max_tokens: 2000
    anthropic:
      api_key: ${ANTHROPIC_API_KEY}
      model: claude-3-5-sonnet-20241022
    ollama:
      base_url: http://localhost:11434
      model: llama3

embeddings:
  default_provider: openai
  providers:
    openai:
      api_key: ${OPENAI_API_KEY}
      model: text-embedding-3-small
      dimension: 1536
    cohere:
      api_key: ${COHERE_API_KEY}
      model: embed-english-v3.0
      dimension: 1024
    local:
      model: all-MiniLM-L6-v2
      dimension: 384

rag:
  context_max_tokens: 4000
  retrieval_top_k: 10
  reranking_enabled: true

agents:
  experiment_analyst:
    enabled: true
    prompts_version: "1.0.0"
  paper_writer:
    enabled: true
    prompts_version: "1.0.0"

cost_controls:
  enabled: true
  monthly_budget_usd: 10000
  max_tokens_per_request: 8000
  alert_threshold_percent: 80
```

---

## Cost Guard Rails

```python
# src/infrastructure/ai/cost_guard.py

from dataclasses import dataclass
from datetime import datetime
from redis.asyncio import Redis

@dataclass
class CostConfig:
    monthly_budget_usd: float
    max_tokens_per_request: int
    input_cost_per_1k: float
    output_cost_per_1k: float

PROVIDER_COSTS = {
    'openai': {
        'gpt-4o': CostConfig(
            monthly_budget_usd=10000,
            max_tokens_per_request=8000,
            input_cost_per_1k=0.0025,
            output_cost_per_1k=0.01
        ),
        'gpt-4o-mini': CostConfig(
            monthly_budget_usd=5000,
            max_tokens_per_request=16000,
            input_cost_per_1k=0.00015,
            output_cost_per_1k=0.0006
        )
    },
    'anthropic': {
        'claude-3-5-sonnet-20241022': CostConfig(
            monthly_budget_usd=10000,
            max_tokens_per_request=8000,
            input_cost_per_1k=0.003,
            output_cost_per_1k=0.015
        )
    }
}

class LLMCostGuard:
    """
    Enforce cost limits on LLM usage.
    
    Critical to prevent runaway costs.
    """
    
    def __init__(
        self,
        redis: Redis,
        organization_id: str,
        provider: str,
        model: str
    ):
        self.redis = redis
        self.org_id = organization_id
        self.provider = provider
        self.model = model
        self.config = PROVIDER_COSTS[provider][model]
    
    async def check_budget(self) -> tuple[bool, float]:
        """
        Check if organization is within budget.
        
        Returns:
            (allowed: bool, remaining_budget: float)
        """
        month_key = f"llm:cost:{self.org_id}:{datetime.utcnow().strftime('%Y-%m')}"
        
        current_cost = float(await self.redis.get(month_key) or 0)
        remaining = self.config.monthly_budget_usd - current_cost
        
        return current_cost < self.config.monthly_budget_usd, remaining
    
    async def record_usage(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Record token usage and return cost.
        """
        month_key = f"llm:cost:{self.org_id}:{datetime.utcnow().strftime('%Y-%m')}"
        
        cost = (
            (input_tokens / 1000) * self.config.input_cost_per_1k +
            (output_tokens / 1000) * self.config.output_cost_per_1k
        )
        
        await self.redis.incrbyfloat(month_key, cost)
        await self.redis.expire(month_key, 86400 * 35)  # 35 days
        
        return cost
    
    def validate_request(self, prompt_tokens: int) -> None:
        """
        Validate request before sending to LLM.
        
        Raises:
            BudgetExceeded: Monthly budget exceeded
            RequestTooLarge: Token limit exceeded
        """
        if prompt_tokens > self.config.max_tokens_per_request:
            raise RequestTooLarge(
                f"Prompt ({prompt_tokens} tokens) exceeds limit "
                f"({self.config.max_tokens_per_request})"
            )


class BudgetExceeded(Exception):
    """Monthly LLM budget exceeded"""
    pass


class RequestTooLarge(Exception):
    """Request exceeds token limit"""
    pass
```

### Embedding Cache

```python
# src/infrastructure/ai/embedding_cache.py

import hashlib
import json
from redis.asyncio import Redis

class EmbeddingCache:
    """
    Cache embeddings to reduce API costs.
    
    Cache hit rate typically 60-80% for search queries.
    """
    
    def __init__(
        self,
        redis: Redis,
        ttl: int = 3600,  # 1 hour
        organization_id: str = None
    ):
        self.redis = redis
        self.ttl = ttl
        self.org_id = organization_id
    
    def _cache_key(self, text: str) -> str:
        """Generate cache key from text"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"embedding:{self.org_id}:{text_hash}"
    
    async def get(self, text: str) -> list[float] | None:
        """Get cached embedding if exists"""
        key = self._cache_key(text)
        cached = await self.redis.get(key)
        
        if cached:
            metrics.increment("embedding.cache.hit")
            return json.loads(cached)
        
        metrics.increment("embedding.cache.miss")
        return None
    
    async def get_or_compute(
        self,
        text: str,
        compute_fn: callable
    ) -> list[float]:
        """
        Get cached embedding or compute and cache.
        
        Args:
            text: Text to embed
            compute_fn: Async function that returns embedding
        
        Returns:
            Embedding vector
        """
        cached = await self.get(text)
        if cached is not None:
            return cached
        
        # Compute
        embedding = await compute_fn([text])
        
        # Cache
        key = self._cache_key(text)
        await self.redis.setex(
            key,
            self.ttl,
            json.dumps(embedding[0])
        )
        
        return embedding[0]
    
    async def warm_cache(self, queries: list[str]) -> None:
        """
        Pre-populate cache with common queries.
        """
        for query in queries:
            # Check if already cached
            if await self.get(query) is None:
                # Compute and cache
                pass
```

---

## Monitoring & Observability

```python
# Track LLM usage
metrics.track("llm.request", {
    "provider": "openai",
    "model": "gpt-4o",
    "tokens": response.usage.total_tokens,
    "latency_ms": elapsed_ms
})

# Track agent performance
metrics.track("agent.invoke", {
    "agent": "experiment_analyst",
    "intent": "experiment_analysis",
    "retrieval_count": len(contexts),
    "tokens_used": token_count
})
```

---

## Next Steps

- Search architecture → [06-search-architecture.md](./06-search-architecture.md)
- Event architecture → [09-event-architecture.md](./09-event-architecture.md)
