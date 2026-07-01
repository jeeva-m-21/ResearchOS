# mypy: disable-error-code="untyped-decorator"
from fastapi import APIRouter

router = APIRouter(tags=["ask"])


@router.get("/ask/ping")
def ping() -> dict[str, str]:
    return {"router": "ask"}
