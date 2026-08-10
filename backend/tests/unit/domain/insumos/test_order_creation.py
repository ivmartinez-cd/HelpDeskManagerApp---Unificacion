"""Tests de caracterización de CanalDirectoOrderCreation — port de los tests de
creación de test_canal_directo_soap_client.py del legacy, contra fakes de los puertos."""

from datetime import datetime

import pytest

from src.modules.insumos.domain.errors import (
    DatosDeContactoIncompletosError,
    PedidoNoConfirmadoError,
    PedidoNoVerificadoError,
    SerieNoActivaEnCanalDirectoError,
)
from src.modules.insumos.domain.services.order_creation import CanalDirectoOrderCreation
from src.modules.insumos.domain.value_objects.cd_datetime import CD_TIMEZONE
from src.modules.insumos.domain.value_objects.cd_supply import CdMachine, CdSupply
from src.modules.insumos.domain.value_objects.order_request import (
    ContactInfo,
    OrderLine,
    OrderRequest,
)
from src.modules.insumos.domain.value_objects.supply_id import ean_check_digit
from tests.unit.domain.insumos.fakes import FakeSupplyCacheRepository, FakeWsAycGateway, settings

# En los tests no se espera de verdad: un solo intento inmediato salvo que el test
# pruebe el reintento explícitamente.
_NO_WAIT = (0,)


def _order(**overrides: object) -> OrderRequest:
    base: dict[str, object] = {
        "customer_id": 1,
        "customer_name": "Cliente Test",
        "store_name": "Sucursal Test",
        "device_serial": "SERIE1",
        "lines": (OrderLine(sku="CF230A", quantity=1, description="Cartucho negro HP 30A"),),
        "reference": "SDS-123",
    }
    base.update(overrides)
    return OrderRequest(**base)  # type: ignore[arg-type]


def _service(
    gateway: FakeWsAycGateway,
    cache: FakeSupplyCacheRepository,
    delays: tuple[float, ...] = _NO_WAIT,
) -> CanalDirectoOrderCreation:
    return CanalDirectoOrderCreation(gateway, cache, settings(), verify_delays=delays)


# --- camino feliz ----------------------------------------------------------------------


async def test_create_order_ok_devuelve_id_con_digito_verificador() -> None:
    gateway = FakeWsAycGateway()
    service = _service(gateway, FakeSupplyCacheRepository())

    order_id = await service.create_order(_order())

    assert order_id == f"441770-{ean_check_digit(441770)}"

    # origen_id viaja en la RAÍZ del payload (no solo anidado en Supply) — es el objetivo
    # entero de usar el SOAP: wsAyC_server.php lee $supply['origen_id'].
    payload = gateway.persisted_payloads[0]
    assert payload["origen_id"] == "3"
    supply_section = payload["Supply"]
    assert isinstance(supply_section, dict)
    assert supply_section["origen_id"] == "3"
    assert supply_section["Revision"] == "1"
    assert supply_section["NroIncidenteCliente"] == "SDS-123"
    assert payload["Detail"] == [
        {"familia_id": "255", "insumo_id": "3729", "cantidad": "1", "motivo_id": "1"}
    ]


async def test_create_order_siembra_supply_cache() -> None:
    """Sembrar supply_serial_cache al crear, sin esperar al próximo ciclo del scan (los
    pedidos con origen Interno no aparecen en getTopSupplies)."""
    gateway = FakeWsAycGateway()
    cache = FakeSupplyCacheRepository()
    service = _service(gateway, cache)

    await service.create_order(_order())

    assert len(cache.entries) == 1
    entry = cache.entries[0]
    assert entry.supply_id == 441770
    assert entry.estado == "Pendiente"
    assert entry.description == "HP E50145/52645 - Toner"
    # La fecha CD ("31/07/2026 10:00:00", hora Argentina) se persiste parseada.
    assert entry.fecha == datetime(2026, 7, 31, 10, 0, 0, tzinfo=CD_TIMEZONE)


# --- serie no activa -------------------------------------------------------------------


async def test_create_order_serie_sin_maquina_levanta_serie_no_activa() -> None:
    gateway = FakeWsAycGateway()
    gateway.machine = None
    service = _service(gateway, FakeSupplyCacheRepository())

    with pytest.raises(SerieNoActivaEnCanalDirectoError):
        await service.create_order(_order())


async def test_create_order_maquina_sin_familia_levanta_serie_no_activa() -> None:
    """Equipo existe pero sin artículo/familia asignada (ej. recién dado de alta)."""
    gateway = FakeWsAycGateway()
    gateway.machine = CdMachine(familia_id="", empresa_id="8")
    service = _service(gateway, FakeSupplyCacheRepository())

    with pytest.raises(SerieNoActivaEnCanalDirectoError):
        await service.create_order(_order())


# --- persistNewSupply devolvió 0 (falló) -----------------------------------------------


async def test_create_order_persist_devuelve_cero_levanta() -> None:
    gateway = FakeWsAycGateway()
    gateway.persist_result = 0
    service = _service(gateway, FakeSupplyCacheRepository())

    with pytest.raises(PedidoNoConfirmadoError, match="no confirmó"):
        await service.create_order(_order())


# --- verificación post-creación --------------------------------------------------------


async def test_create_order_referencia_no_coincide_levanta() -> None:
    """El ID sale de un MAX+1 sin lock (carrera posible del lado del servidor): si al
    releer el pedido su NroIncidenteCliente no es el nuestro, no confiamos en el ID."""
    gateway = FakeWsAycGateway()
    gateway.default_supply = CdSupply(supply_id=441770, reference="SDS-OTRO", fecha="x")
    cache = FakeSupplyCacheRepository()
    service = _service(gateway, cache)

    with pytest.raises(PedidoNoVerificadoError, match="No se pudo verificar"):
        await service.create_order(_order())

    # No debe haber sembrado el cache con un pedido que no pudo verificar como propio.
    assert cache.entries == []


async def test_create_order_pedido_no_existe_al_releer_levanta() -> None:
    """getSupplyById devuelve "[]" cuando el ID no existe — la serie no existía, el
    INSERT...SELECT no insertó filas, pero persistNewSupply igual devolvió un ID."""
    gateway = FakeWsAycGateway()
    gateway.default_supply = None
    service = _service(gateway, FakeSupplyCacheRepository())

    with pytest.raises(PedidoNoVerificadoError, match="No se pudo verificar"):
        await service.create_order(_order())


async def test_create_order_reintenta_verificacion_si_todavia_no_lo_ve() -> None:
    """Caso real (pedido 443017/SDS-974325, 2026-08-03): persistNewSupply creó el pedido
    pero la primera lectura de getSupplyById todavía no lo veía (lag de Canal Directo)."""
    gateway = FakeWsAycGateway()
    gateway.supply_reads = [None]  # la primera lectura no lo ve; la segunda usa el default
    service = _service(gateway, FakeSupplyCacheRepository(), delays=(0, 0))

    order_id = await service.create_order(_order())

    assert order_id
    assert len(gateway.fetch_calls) == 2  # falló la primera lectura, la segunda ya lo vio


# --- datos de contacto faltantes -------------------------------------------------------


async def test_create_order_sin_contacto_ni_config_levanta_con_campos_faltantes() -> None:
    gateway = FakeWsAycGateway()
    service = CanalDirectoOrderCreation(
        gateway,
        FakeSupplyCacheRepository(),
        settings(solicitante=ContactInfo()),
        verify_delays=_NO_WAIT,
    )

    with pytest.raises(DatosDeContactoIncompletosError, match="solicitante_nombre/apellido"):
        await service.create_order(_order())

    # Nunca debe llegar a crear el pedido si los contactos están incompletos.
    assert gateway.persisted_payloads == []
