import uuid
from datetime import date

from src.modules.prestadores.application.use_cases.list_asignacion_overrides import (
    ListAsignacionOverrides,
    ListAsignacionOverridesDependencies,
)
from src.modules.prestadores.domain.entities.asignacion_override import AsignacionOverride
from tests.unit.domain.prestadores.fakes import FakeAsignacionOverrideRepository, FakeUserProvider


def _override(desde: date, **overrides: object) -> AsignacionOverride:
    base = {
        "id": uuid.uuid4(),
        "operador_ausente_id": uuid.uuid4(),
        "operador_reemplazante_id": uuid.uuid4(),
        "desde": desde,
        "hasta": date(2026, 12, 31),
        "alcance": "TOTAL",
        "estado": "ACTIVA",
        "motivo": None,
        "created_by_user_id": uuid.uuid4(),
    }
    base.update(overrides)
    return AsignacionOverride(**base)  # type: ignore[arg-type]


async def test_lista_ordenada_por_desde_mas_reciente_primero() -> None:
    repo = FakeAsignacionOverrideRepository()
    viejo = _override(date(2026, 1, 1))
    nuevo = _override(date(2026, 8, 1))
    repo.rows[viejo.id] = viejo
    repo.rows[nuevo.id] = nuevo

    resultado = await ListAsignacionOverrides(
        ListAsignacionOverridesDependencies(overrides=repo, users=FakeUserProvider())
    ).execute()

    assert [dto.id for dto in resultado] == [nuevo.id, viejo.id]
