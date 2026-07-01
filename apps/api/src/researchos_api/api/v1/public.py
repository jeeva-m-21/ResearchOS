# mypy: disable-error-code="untyped-decorator"
from fastapi import APIRouter

router = APIRouter(tags=["public"])


@router.get("/public/ping")
def ping() -> dict[str, str]:
    return {"router": "public"}
