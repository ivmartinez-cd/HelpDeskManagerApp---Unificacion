from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/health", tags=["health"])


class EchoRequest(BaseModel):
    message: str = Field(min_length=1)


@router.get("")
def get_health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@router.post("/echo")
def post_echo(payload: EchoRequest) -> dict[str, str]:
    """Sonda del envelope de errores de validación (la usa
    tests/integration/test_error_handling.py): un endpoint con body mínimo que
    dispara un 422 reproducible. Sin auth a propósito — no expone datos."""
    return {"message": payload.message}


@router.get("/db")
async def get_health_db(db: AsyncSession = Depends(get_db, scope="function")) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}
