# mypy: disable-error-code="untyped-decorator"
from fastapi import APIRouter

router = APIRouter(tags=["ingest"])


@router.get("/ingest/ping")
def ping() -> dict[str, str]:
    return {"router": "ingest"}
