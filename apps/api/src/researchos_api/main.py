# mypy: disable-error-code="untyped-decorator"
from fastapi import FastAPI

from .api.v1 import ask, experiments, ingest, public, search


def create_app() -> FastAPI:
    app = FastAPI(title="Research OS API", version="0.1.0")
    for mod in (experiments, ingest, search, ask):
        app.include_router(mod.router, prefix="/v1")
    app.include_router(public.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
