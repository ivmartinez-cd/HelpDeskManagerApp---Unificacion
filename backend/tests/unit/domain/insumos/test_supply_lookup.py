"""Tests de caracterización de CanalDirectoSupplyLookup — port de los tests de lectura
de test_canal_directo_soap_client.py del legacy (lookup, reconcile, descripción)."""

import pytest

from src.modules.insumos.domain.errors import ConsultaDePedidosNoDisponibleError
from src.modules.insumos.domain.services.supply_lookup import CanalDirectoSupplyLookup
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, CdSupply
from tests.unit.domain.insumos.fakes import FakeSupplyCacheRepository, FakeWsAycGateway, settings


def _lookup(
    gateway: FakeWsAycGateway, cache: FakeSupplyCacheRepository
) -> CanalDirectoSupplyLookup:
    return CanalDirectoSupplyLookup(gateway, cache, settings())


def _cached(supply_id: int, serial: str = "SERIE1", estado: str = "Pendiente") -> CachedSupply:
    return CachedSupply(supply_id=supply_id, serial=serial, estado=estado, empresa_id="8")


# --- lookup_supplies_by_serial ---------------------------------------------------------


async def test_lookup_combina_cache_local_y_get_top_supplies() -> None:
    cache = FakeSupplyCacheRepository()
    # Entrada del cache local (alimentada por el scan) — la única vía que ve pedidos de
    # origen Interno (getTopSupplies los excluye).
    await cache.upsert([_cached(111)])
    gateway = FakeWsAycGateway()
    gateway.supplies_for_empresa = [
        CdSupply(
            supply_id=222, estado="Pendiente", fecha="31/07/2026", nro_serie_solicitud="SERIE1"
        )
    ]

    result = await _lookup(gateway, cache).lookup_supplies_by_serial("SERIE1")

    assert {r.nro.split("-")[0] for r in result} == {"111", "222"}


async def test_lookup_incluye_fila_de_serie_vacia_como_fail_safe() -> None:
    """Mismo criterio que el portal aplicaba: mejor un falso bloqueo que un duplicado."""
    gateway = FakeWsAycGateway()
    gateway.supplies_for_empresa = [
        CdSupply(supply_id=333, estado="Pendiente", fecha="x", nro_serie_solicitud="")
    ]

    result = await _lookup(gateway, FakeSupplyCacheRepository()).lookup_supplies_by_serial("SERIE1")

    assert len(result) == 1
    assert result[0].nro.startswith("333")


async def test_lookup_excluye_estados_terminales() -> None:
    cache = FakeSupplyCacheRepository()
    await cache.upsert([_cached(111, estado="Anulado"), _cached(112, estado="Entregado")])
    gateway = FakeWsAycGateway()

    assert await _lookup(gateway, cache).lookup_supplies_by_serial("SERIE1") == []


async def test_lookup_ambas_fuentes_fallan_con_raise_on_error_propaga() -> None:
    gateway = FakeWsAycGateway()
    gateway.machine_error = ConnectionError("timeout")
    cache = FakeSupplyCacheRepository()
    cache.get_error = RuntimeError("db down")

    with pytest.raises(ConsultaDePedidosNoDisponibleError, match="No se pudieron consultar"):
        await _lookup(gateway, cache).lookup_supplies_by_serial("SERIE1", raise_on_error=True)


async def test_lookup_una_sola_fuente_caida_no_propaga() -> None:
    """Que una de las dos fuentes ande ya alcanza para no arriesgar un duplicado."""
    gateway = FakeWsAycGateway()
    gateway.machine_error = ConnectionError("timeout")
    cache = FakeSupplyCacheRepository()
    await cache.upsert([_cached(111)])

    result = await _lookup(gateway, cache).lookup_supplies_by_serial("SERIE1", raise_on_error=True)

    assert len(result) == 1


async def test_lookup_serie_vacia_no_consulta_nada() -> None:
    gateway = FakeWsAycGateway()
    gateway.machine_error = AssertionError("no debería llamar al SOAP con serie vacía")
    cache = FakeSupplyCacheRepository()
    cache.get_error = AssertionError("no debería consultar el cache con serie vacía")

    assert await _lookup(gateway, cache).lookup_supplies_by_serial("   ") == []


# --- find_order_by_reference: reconciliación manual ------------------------------------


async def test_find_order_by_reference_encuentra_por_referencia_exacta() -> None:
    """Caso real: pedido 443017/SDS-974325 cacheado por el scan periódico — se relee
    fresco y se confirma la referencia exacta antes de devolverlo."""
    cache = FakeSupplyCacheRepository()
    await cache.upsert([_cached(443016, serial="BRBST290BN"), _cached(443017, serial="BRBST290BN")])
    gateway = FakeWsAycGateway()
    gateway.supplies_by_id = {
        443016: CdSupply(supply_id=443016, reference="SDS-OTRO", estado="Pendiente"),
        443017: CdSupply(supply_id=443017, reference="SDS-974325", estado="Pendiente"),
    }

    result = await _lookup(gateway, cache).find_order_by_reference("BRBST290BN", "SDS-974325")

    assert result is not None
    assert result.supply_id == 443017


async def test_find_order_by_reference_ignora_candidatos_anulados_o_cancelados() -> None:
    """Un pedido Anulado/Cancelado nunca debe vincularse, aunque su referencia matchee
    (ej. se anuló a mano por error y se recreó con otro ID)."""
    cache = FakeSupplyCacheRepository()
    await cache.upsert([_cached(500, estado="Anulado")])
    gateway = FakeWsAycGateway()

    assert await _lookup(gateway, cache).find_order_by_reference("SERIE1", "SDS-500") is None
    assert gateway.fetch_calls == []  # el candidato descartado por estado no se relee


async def test_find_order_by_reference_sin_candidatos_devuelve_none() -> None:
    gateway = FakeWsAycGateway()

    result = await _lookup(gateway, FakeSupplyCacheRepository()).find_order_by_reference(
        "SERIE-SIN-CACHE", "SDS-999"
    )

    assert result is None


async def test_find_order_by_reference_ninguno_matchea_devuelve_none() -> None:
    cache = FakeSupplyCacheRepository()
    await cache.upsert([_cached(700)])
    gateway = FakeWsAycGateway()
    gateway.supplies_by_id = {
        700: CdSupply(supply_id=700, reference="SDS-OTRO", estado="Pendiente")
    }

    assert await _lookup(gateway, cache).find_order_by_reference("SERIE1", "SDS-500") is None


# --- fetch_supply_article_description --------------------------------------------------


async def test_fetch_supply_article_description_ok() -> None:
    gateway = FakeWsAycGateway()
    lookup = _lookup(gateway, FakeSupplyCacheRepository())

    assert await lookup.fetch_supply_article_description("441770-3") == "HP E50145/52645 - Toner"
    assert gateway.description_calls == [441770]


async def test_fetch_supply_article_description_sin_detalle_devuelve_vacio() -> None:
    gateway = FakeWsAycGateway()
    gateway.description = ""
    lookup = _lookup(gateway, FakeSupplyCacheRepository())

    assert await lookup.fetch_supply_article_description("441770-3") == ""


async def test_fetch_supply_article_description_id_vacio_no_llama_red() -> None:
    gateway = FakeWsAycGateway()
    lookup = _lookup(gateway, FakeSupplyCacheRepository())

    assert await lookup.fetch_supply_article_description("  ") == ""
    assert gateway.description_calls == []
