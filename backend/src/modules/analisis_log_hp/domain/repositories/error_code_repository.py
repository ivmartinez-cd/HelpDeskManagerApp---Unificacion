"""Puerto: catálogo de códigos de error HP."""

from typing import Any, Protocol

from src.modules.analisis_log_hp.domain.entities.error_code import ErrorCode


class ErrorCodeRepository(Protocol):
    async def get_by_code(self, code: str) -> ErrorCode | None: ...

    async def get_by_codes(self, codes: list[str]) -> dict[str, ErrorCode]: ...

    async def upsert(
        self,
        code: str,
        *,
        severity: str | None = None,
        description: str | None = None,
        solution_url: str | None = None,
        solution_content: str | None = None,
    ) -> ErrorCode: ...

    async def list_page(self, page: int, size: int) -> tuple[list[ErrorCode], int]: ...

    async def bulk_update_solution_urls(
        self, updates: dict[str, dict[str, Any]]
    ) -> int: ...
