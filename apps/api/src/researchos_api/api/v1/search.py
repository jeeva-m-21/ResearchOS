# mypy: disable-error-code="untyped-decorator"
from fastapi import APIRouter

router = APIRouter(tags=["search"])


@router.get("/search/ping")
def ping() -> dict[str, str]:
    return {"router": "search"}
