# STATE.md

## Current Sprint: T-026 — Research AI Chat Assistant

**Goal**: Build a research-aware AI chat assistant in the dashboard that can read/query experiments, notebooks, and search — with model selection (OpenAI, Anthropic, Ollama).

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

app/dashboard/ask/
  └── page.tsx            # Dedicated AI chat page

components/ai/
  ├── ChatPanel.tsx       # Main chat panel (messages + input + model selector)
  ├── ChatMessage.tsx     # Single message bubble (markdown rendered)
  ├── ChatInput.tsx       # Input area with send + model selector
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

### Plan
1. ✅ Add `openai` + `anthropic` to `pyproject.toml`
2. ✅ Create `application/ai/dto.py` — AskRequest, AskResponse, ChatMessage, ModelInfo
3. ✅ Create `application/ai/tools.py` — Tool registry with 6 research tools
4. ✅ Create `application/ai/orchestrator.py` — AIOrchestrator (tool loop + SSE streaming)
5. ✅ Create `infrastructure/adapters/llm/base.py` — LLMProvider ABC
6. ✅ Create `infrastructure/adapters/llm/openai.py` — OpenAI provider
7. ✅ Create `infrastructure/adapters/llm/anthropic.py` — Anthropic provider
8. ✅ Create `infrastructure/adapters/llm/ollama.py` — Ollama provider
9. ✅ Create `api/routes/ask.py` — POST /v1/ask (SSE) + GET /v1/ask/models
10. ✅ Wire ask router into app
11. ✅ Install `react-markdown`, `remark-gfm`, `@tailwindcss/typography` on frontend
12. ✅ Create frontend `lib/api/ask.ts`
13. ✅ Create frontend AI chat components (ChatMessage, ModelSelector, ChatInput, ChatPanel)
14. ✅ Create frontend `/dashboard/ask` page + add AI nav item
15. ✅ Write tests for AI orchestration + tools (16 tests)
16. ✅ Run feedback loop: ruff + mypy + pytest + tsc + build

### Done
- T-026 — Research AI Chat Assistant (backend + frontend + tests)

### Next Steps (after this sprint)
- T-027: Write tools (create/update notebook blocks from chat)
- T-028: Context-aware system prompt with project/org context
- T-029: Floating chat panel (slide-over from any dashboard page)
- Artifact frontend

### Next Steps (after this sprint)
- T-027: Write tools (create/update notebook blocks from chat)
- T-028: Context-aware system prompt with project/org context
- T-029: Floating chat panel (slide-over from any dashboard page)
- Artifact frontend
