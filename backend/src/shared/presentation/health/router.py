from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/health", tags=["health"])


class EchoRequest(BaseModel):
    message: str = Field(min_length=1)


@router.get("")
def get_health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@router.post("/echo")
def post_echo(payload: EchoRequest) -> dict[str, str]:
    return {"message": payload.message}
