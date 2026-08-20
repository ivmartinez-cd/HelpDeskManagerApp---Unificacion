import uuid
from datetime import date
from unittest.mock import AsyncMock

import pytest

from src.modules.contadores.application.use_cases.list_asignacion_overrides import (
    ListAsignacionOverrides,
    ListAsignacionOverridesDependencies,
)
from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride


def _override(desde: date, **overrides: object) -> AsignacionOverride:
    base = {
        "id": uuid.uuid4(),
        "operador_ausente_id": "mjvela",
        "operador_reemplazante_id": "vipaez",
        "desde": desde,
        "hasta": date(2026, 12, 31),
        "alcance": "TOTAL",
        "estado": "ACTIVA",
        "motivo": None,
        "created_by_user_id": uuid.uuid4(),
    }
    base.update(overrides)
    return AsignacionOverride(**base)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_lista_ordenada_por_vigente_desde_mas_reciente_primero() -> None:
    viejo = _override(date(2026, 1, 1))
    nuevo = _override(date(2026, 8, 1))
    overrides = AsyncMock()
    overrides.list_all.return_value = [viejo, nuevo]
    calendar = AsyncMock()
    calendar.list_operadores.return_value = []

    resultado = await ListAsignacionOverrides(
        ListAsignacionOverridesDependencies(overrides=overrides, calendar=calendar)
    ).execute()

    assert [dto.id for dto in resultado] == [nuevo.id, viejo.id]
