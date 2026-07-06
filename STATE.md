# STATE.md

## Current Sprint: T-025 — Compute Factory Backend

**Goal**: Build a pluggable compute factory for notebook block execution. Abstract away execution backends (in-app subprocess, local Jupyter, cloud GCP) behind a clean provider interface. This is the first step toward a Colab-like execution experience.

### Design

```
application/compute/
  ├── dto.py          # ExecutionRequest, ExecutionResult
  ├── provider.py     # ComputeProvider ABC (interface)
  └── factory.py      # ComputeFactory — register & resolve providers

infrastructure/compute/
  └── in_app.py       # InAppProvider — wraps existing subprocess executor

api/routes/notebooks.py
  └── execute endpoint → uses ComputeFactory
```

### Plan
1. Create `application/compute/dto.py` — ExecutionRequest/Result Pydantic models
2. Create `application/compute/provider.py` — ComputeProvider abstract base class
3. Create `application/compute/factory.py` — ComputeFactory with register/get
4. Create `infrastructure/compute/in_app.py` — InAppProvider (refactors existing executor logic into the interface)
5. Add Alembic migration: `compute_provider` column to notebooks table (default "in_app")
6. Update `POST /v1/notebooks/{id}/blocks/{bid}/execute` to accept `?provider=in_app` query param and use factory
7. Write tests for factory resolution + InAppProvider execution
8. Run feedback loop: ruff + mypy + pytest

### Done
- T-019 through T-024

### Next Steps (after this sprint)
- T-026: Local Jupyter compute provider
- T-027: Colab-like notebook editor frontend (Monaco editor, cell toolbar, rich output)
- Artifact frontend
