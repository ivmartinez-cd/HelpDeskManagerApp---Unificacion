from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def get_health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
