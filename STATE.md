# STATE.md

## Current Sprint: T-026 — Research AI Chat Assistant

**Goal**: Build a research-aware AI chat assistant in the dashboard that can read/query experiments, notebooks, and search — with model selection (OpenAI, Anthropic, Ollama).

### Layout

```
/dashboard                  → Centered AI chat (main landing page, Claude-like)
/dashboard/analytics        → Analytics overview (stats, activity, quick actions)
/dashboard/experiments      → Experiment management
/dashboard/notebooks        → Notebook management
/dashboard/papers           → Papers (upcoming)
/dashboard/search           → Hybrid search
```

### Architecture

```
Backend — Hexagonal layers:

application/ai/
  ├── dto.py              # AskRequest, AskResponse, ChatMessage, ModelInfo
  ├── tools.py            # ResearchTool ABC + implementations (search, get_experiment, get_notebook, list_*)
  └── orchestrator.py     # AIOrchestrator — manages conversation, calls LLM, executes tools, streams

infrastructure/adapters/llm/
  ├── __init__.py
  ├── base.py             # LLMProvider ABC (interface)
  ├── openai.py           # OpenAI provider
  ├── anthropic.py        # Anthropic provider
  └── ollama.py           # Ollama local provider

api/routes/ask.py         # POST /v1/ask (SSE streaming), GET /v1/ask/models

Frontend:

app/dashboard/
  ├── page.tsx            # Centered AI chat (main landing page)
  └── analytics/
      └── page.tsx        # Analytics overview

components/ai/
  ├── ChatPanel.tsx       # Main chat panel (centered, Claude-like)
  ├── ChatMessage.tsx     # Single message bubble (markdown rendered)
  ├── ChatInput.tsx       # Clean input area with send button inside
  └── ModelSelector.tsx   # Model selection dropdown

lib/api/ask.ts            # API client for ask endpoint + models listing
```

### Tools (read-only for MVP)
1. `search_research(query, types?, limit?)` — Hybrid search across all research objects
2. `get_experiment(experiment_id)` — Experiment details with runs and metrics
3. `get_notebook(notebook_id)` — Notebook with block contents
4. `list_experiments(project_id?, limit?, offset?)` — List experiments in project
5. `list_notebooks(project_id?, limit?, offset?)` — List notebooks in project
6. `get_block_content(block_id)` — Get specific block content

### Done
- T-026 — Research AI Chat Assistant (backend + frontend + tests)
- Layout redesign: chat is main landing page, analytics moved to /dashboard/analytics

### Next Steps (after this sprint)
- T-027: Write tools (create/update notebook blocks from chat)
- T-028: Context-aware system prompt with project/org context
- T-029: Floating chat panel (slide-over from any dashboard page)
- Artifact frontend
