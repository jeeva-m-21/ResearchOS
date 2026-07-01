# mypy: disable-error-code="untyped-decorator"
from fastapi import APIRouter

router = APIRouter(tags=["experiments"])


@router.get("/experiments/ping")
def ping() -> dict[str, str]:
    return {"router": "experiments"}
