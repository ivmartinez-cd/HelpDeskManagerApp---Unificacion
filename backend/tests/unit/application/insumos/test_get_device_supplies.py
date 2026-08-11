"""Tests de GetDeviceSupplies — historial de pedidos de una serie (3 fuentes mergeadas)."""

from datetime import UTC, datetime

from src.modules.insumos.application.use_cases.get_device_supplies import (
    GetDeviceSupplies,
    GetDeviceSuppliesPorts,
)
from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, CdSupply
from tests.unit.domain.insumos.fakes import (
    FakeProcessedRequestRepository,
    FakeSupplyCacheRepository,
    FakeWsAycGateway,
    settings,
)

SERIAL = "MXBCQ7C03T"


class World:
    def __init__(self) -> None:
        self.wsayc = FakeWsAycGateway()
        self.cache = FakeSupplyCacheRepository()
        self.processed = FakeProcessedRequestRepository()
        # Sin fuentes por default: cada test arma exactamente lo suyo.
        self.wsayc.default_supply = None
        self.wsayc.descriptions_by_id = {}
        self.use_case = GetDeviceSupplies(
            GetDeviceSuppliesPorts(
                wsayc=self.wsayc,  # type: ignore[arg-type]
                supply_cache=self.cache,  # type: ignore[arg-type]
                processed=self.processed,  # type: ignore[arg-type]
            ),
            settings(),
        )


def _portal_supply(supply_id: int, serial: str = SERIAL, **overrides: object) -> CdSupply:
    base: dict[str, object] = {
        "supply_id": supply_id,
        "estado": "Pendiente",
        "fecha": "01/08/2026 10:00:00",
        "nro_serie_solicitud": serial,
        "sku": "CF230A",
        "descripcion": "Toner HP 30A",
    }
    base.update(overrides)
    return CdSupply(**base)  # type: ignore[arg-type]


def _cached(supply_id: int, **overrides: object) -> CachedSupply:
    base: dict[str, object] = {
        "supply_id": supply_id,
        "serial": SERIAL,
        "estado": "Entregado",
        "fecha": datetime(2026, 7, 15, 13, 0, tzinfo=UTC),
    }
    base.update(overrides)
    return CachedSupply(**base)  # type: ignore[arg-type]


async def _mark_own(world: World, hp_request_id: int, order_id: str) -> None:
    await world.processed.mark_processed(
        ProcessedRequest(
            hp_request_id=hp_request_id,
            device_serial=SERIAL,
            sku="W9008MC",
            internal_order_id=order_id,
            description="Toner W9008MC",
            created_at=datetime(2026, 8, 1, 12, 30, tzinfo=UTC),
        )
    )


async def test_mergea_las_tres_fuentes_y_ordena_por_supply_id_desc() -> None:
    world = World()
    world.wsayc.supplies_for_empresa = [_portal_supply(441800)]
    world.cache.entries.append(_cached(441500))
    await _mark_own(world, 974325, "441900-1")
    world.wsayc.supplies_by_id = {441900: _portal_supply(441900, estado="Despachado")}

    rows = await world.use_case.execute(SERIAL, limit=10)

    assert [r.supply_id for r in rows] == [441900, 441800, 441500]
    assert [r.source for r in rows] == ["local", "soap", "local"]


async def test_el_soap_gana_ante_duplicados_pero_toma_sku_propio_de_respaldo() -> None:
    """El mismo pedido puede venir por getTopSupplies y estar en processed_requests —
    la fila SOAP tiene más campos, pero sku/descripción propios rellenan los vacíos."""
    world = World()
    world.wsayc.supplies_for_empresa = [_portal_supply(441800, sku="", descripcion="")]
    world.cache.entries.append(_cached(441800, estado="Pendiente"))
    await _mark_own(world, 974325, "441800-2")

    rows = await world.use_case.execute(SERIAL, limit=10)

    assert len(rows) == 1
    row = rows[0]
    assert row.source == "soap"
    assert row.sku == "W9008MC"
    assert row.descripcion == "Toner W9008MC"
    assert world.wsayc.fetch_calls == []  # ya visto: no se reconsulta en vivo


async def test_pedido_propio_invisible_se_reconfirma_en_vivo_y_siembra_el_cache() -> None:
    """Fuente 3: pedidos de origen Interno tan nuevos que ni el scan los vio — se
    reconfirman por getSupplyById y el estado fresco queda cacheado."""
    world = World()
    await _mark_own(world, 974325, "441900-1")
    world.wsayc.supplies_by_id = {
        441900: _portal_supply(441900, estado="Despachado", empresa_id="8")
    }

    rows = await world.use_case.execute(SERIAL, limit=10)

    assert rows[0].estado == "Despachado"
    assert rows[0].fecha == "01/08/2026 10:00:00"
    cached = [e for e in world.cache.entries if e.supply_id == 441900]
    assert len(cached) == 1 and cached[0].estado == "Despachado"


async def test_pedido_propio_que_el_soap_no_ve_queda_pendiente_con_fecha_propia() -> None:
    """Lag de lectura de CD: la app lo creó, existe — nunca se lo esconde."""
    world = World()
    await _mark_own(world, 974325, "441900-1")
    world.wsayc.supplies_by_id = {}

    rows = await world.use_case.execute(SERIAL, limit=10)

    assert rows[0].estado == "Pendiente"
    assert rows[0].fecha == "01/08/2026 09:30:00"  # created_at UTC → hora Argentina
    assert world.cache.entries == []  # sin lectura real no se siembra nada


async def test_dryrun_y_ordenes_no_parseables_quedan_afuera() -> None:
    world = World()
    await _mark_own(world, 974325, "DRYRUN-SDS-974325")

    rows = await world.use_case.execute(SERIAL, limit=10)

    assert rows == []
    assert world.wsayc.fetch_calls == []


async def test_caida_del_soap_no_tira_el_historial_local() -> None:
    """Best-effort: si getMachineBySerial falla, quedan las fuentes locales."""
    world = World()
    world.wsayc.machine_error = ConnectionError("timeout")
    world.cache.entries.append(_cached(441500))

    rows = await world.use_case.execute(SERIAL, limit=10)

    assert [r.supply_id for r in rows] == [441500]


async def test_filtra_por_serie_y_respeta_el_limite() -> None:
    world = World()
    world.wsayc.supplies_for_empresa = [
        _portal_supply(441800),
        _portal_supply(441801, serial="OTRASERIE1"),
        _portal_supply(441700),
        _portal_supply(441600),
    ]

    rows = await world.use_case.execute(SERIAL, limit=2)

    assert [r.supply_id for r in rows] == [441800, 441700]


async def test_series_de_origen_interno_se_extraen_del_texto_libre() -> None:
    """NroSerieSolicitud vacío + serial dentro de NroSerie (pedidos de origen Interno)."""
    world = World()
    world.wsayc.supplies_for_empresa = [
        _portal_supply(
            441800,
            serial="",
            nro_serie=f"Porcentaje: 6\nDias Restantes Est.: 10\n{SERIAL}",
        )
    ]

    rows = await world.use_case.execute(SERIAL, limit=10)

    assert [r.supply_id for r in rows] == [441800]


async def test_descripciones_faltantes_se_enriquecen_y_persisten() -> None:
    """Pedidos externos: el detalle del pedido es la única fuente del consumible real."""
    world = World()
    world.wsayc.supplies_for_empresa = [
        _portal_supply(441800, descripcion=""),
        _portal_supply(441700),
    ]
    world.wsayc.descriptions_by_id = {441800: "Kit de mantenimiento"}

    rows = await world.use_case.execute(SERIAL, limit=10)

    assert rows[0].descripcion == "Kit de mantenimiento"
    assert world.wsayc.description_calls == [441800]  # solo el que faltaba
    assert any(
        e.supply_id == 441800 and e.description == "Kit de mantenimiento"
        for e in world.cache.entries
    )
