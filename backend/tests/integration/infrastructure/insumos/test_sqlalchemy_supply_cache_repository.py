"""Tests de integración de SqlAlchemySupplyCacheRepository contra el Postgres de test.

Verifica la semántica de upsert del legacy (db/supplies.py): serial/estado/fecha se
pisan siempre; empresa_id/sku/description solo si el valor nuevo no es vacío.
"""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.cd_datetime import CD_TIMEZONE
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply
from src.modules.insumos.infrastructure.repositories.sqlalchemy_supply_cache_repository import (
    SqlAlchemySupplyCacheRepository,
)


def _entry(supply_id: int, **overrides: object) -> CachedSupply:
    base: dict[str, object] = {
        "supply_id": supply_id,
        "serial": "SERIE1",
        "estado": "Pendiente",
        "empresa_id": "8",
        "fecha": datetime(2026, 7, 31, 10, 0, 0, tzinfo=CD_TIMEZONE),
        "sku": "CF230A",
        "description": "Toner HP 30A",
    }
    base.update(overrides)
    return CachedSupply(**base)  # type: ignore[arg-type]


async def test_upsert_y_lectura_case_insensitive_ordenada_desc(db_session: AsyncSession) -> None:
    repo = SqlAlchemySupplyCacheRepository(db_session)
    await repo.upsert([_entry(111), _entry(222)])

    rows = await repo.get_by_serial("serie1")

    assert [r.supply_id for r in rows] == [222, 111]
    assert rows[0].serial == "SERIE1"


async def test_upsert_conflicto_pisa_estado_pero_conserva_descripcion_no_vacia(
    db_session: AsyncSession,
) -> None:
    """El scan trae menos datos que la creación (sin description/sku) — actualizar el
    estado del pedido no debe borrar la descripción sembrada al crearlo."""
    repo = SqlAlchemySupplyCacheRepository(db_session)
    await repo.upsert([_entry(111, estado="Pendiente", description="Toner HP 30A")])

    await repo.upsert([_entry(111, estado="Despachado", sku="", description="")])

    rows = await repo.get_by_serial("SERIE1")
    assert rows[0].estado == "Despachado"
    assert rows[0].description == "Toner HP 30A"
    assert rows[0].sku == "CF230A"


async def test_upsert_conflicto_actualiza_descripcion_si_viene_con_valor(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemySupplyCacheRepository(db_session)
    await repo.upsert([_entry(111, description="")])

    await repo.upsert([_entry(111, description="Toner real")])

    rows = await repo.get_by_serial("SERIE1")
    assert rows[0].description == "Toner real"


async def test_get_by_serial_respeta_limit(db_session: AsyncSession) -> None:
    repo = SqlAlchemySupplyCacheRepository(db_session)
    await repo.upsert([_entry(i) for i in range(100, 130)])

    rows = await repo.get_by_serial("SERIE1", limit=5)

    assert [r.supply_id for r in rows] == [129, 128, 127, 126, 125]


async def test_upsert_lista_vacia_no_falla(db_session: AsyncSession) -> None:
    repo = SqlAlchemySupplyCacheRepository(db_session)
    await repo.upsert([])
    assert await repo.get_by_serial("SERIE1") == []


async def test_find_active_by_serial_ignora_estados_terminales(db_session: AsyncSession) -> None:
    """Entregado tampoco es "activo": es cierre exitoso, no bloquea una carga nueva."""
    repo = SqlAlchemySupplyCacheRepository(db_session)
    await repo.upsert(
        [
            _entry(111, estado="Pendiente"),
            _entry(222, estado="Entregado"),
            _entry(333, estado="Anulado"),
        ]
    )

    active = await repo.find_active_by_serial("serie1")

    assert active is not None
    assert active.supply_id == 111


async def test_find_active_by_serial_sin_activos_devuelve_none(db_session: AsyncSession) -> None:
    repo = SqlAlchemySupplyCacheRepository(db_session)
    await repo.upsert([_entry(222, estado="Entregado")])

    assert await repo.find_active_by_serial("SERIE1") is None


async def test_get_status(db_session: AsyncSession) -> None:
    repo = SqlAlchemySupplyCacheRepository(db_session)
    await repo.upsert([_entry(111, estado="Despachado")])

    assert await repo.get_status(111) == "Despachado"
    assert await repo.get_status(999) is None


async def test_upsert_registra_primer_avistaje_de_cada_estado(db_session: AsyncSession) -> None:
    """El historial de transiciones se graba en el upsert, dedup por (supply_id,
    estado): re-escanear el mismo estado mil veces no agrega filas."""
    repo = SqlAlchemySupplyCacheRepository(db_session)
    await repo.upsert([_entry(111, estado="Pendiente")])
    await repo.upsert([_entry(111, estado="Pendiente")])  # repetido: no suma
    await repo.upsert([_entry(111, estado="Despachado"), _entry(222, estado="Pendiente")])

    history = await repo.get_status_history_batch([111, 222, 999])

    assert [e.estado for e in history[111]] == ["Pendiente", "Despachado"]
    assert [e.estado for e in history[222]] == ["Pendiente"]
    assert 999 not in history
    assert history[111][0].first_seen_at <= history[111][1].first_seen_at


async def test_estado_vacio_no_genera_historial(db_session: AsyncSession) -> None:
    repo = SqlAlchemySupplyCacheRepository(db_session)
    await repo.upsert([_entry(111, estado="")])

    assert await repo.get_status_history_batch([111]) == {}


async def test_get_status_history_batch_lista_vacia(db_session: AsyncSession) -> None:
    repo = SqlAlchemySupplyCacheRepository(db_session)
    assert await repo.get_status_history_batch([]) == {}
