"""Tests de AutoLoadRequests — port de maybe_auto_load (config.py del legacy).

Fakes livianos de ListRequests/LoadOrder (Protocols angostos definidos en el propio
caso de uso) en vez de armar las clases reales con todas sus dependencias — acá solo
interesa la orquestación (kill switch, elegibilidad, tope por ciclo, best-effort ante
fallos), no la lógica de fetch ni de bloqueos, ya cubierta por sus propios tests."""

from src.modules.insumos.application.dtos.load_order import LoadOrderCommand, failure, success
from src.modules.insumos.application.dtos.request_rows import RequestRow
from src.modules.insumos.application.use_cases.auto_load_requests import (
    AutoLoadPorts,
    AutoLoadRequests,
)
from tests.unit.domain.insumos.fakes import FakeInsumosSettingsRepository


def _row(request_id: int, **overrides: object) -> RequestRow:
    base: dict[str, object] = {
        "request_id": request_id,
        "device_id": request_id,
        "customer_id": 8,
        "customer_name": "Cliente Test",
        "store": "HANGAR",
        "serial": f"SERIE{request_id}",
        "description": "Cartucho negro HP 30A",
        "sku": "CF230A",
        "percent_left": 5.0,
        "days_left": 2,
        "pages_left": 100,
        "consumable_index": 0,
        "consumable_url": "",
        "time": "10/08 10:00",
        "raw_time": "2026-08-10T10:00:00.000Z",
        "status_key": "critical",
        "status_label": "Crítico",
        "order_id": None,
        "requested_percent": None,
        "requested_days_left": None,
        "last_contact": None,
        "days_offline": None,
        "is_stale_offline": False,
    }
    base.update(overrides)
    return RequestRow(**base)  # type: ignore[arg-type]


class FakeListRequests:
    def __init__(self, rows: list[RequestRow]) -> None:
        self.rows = rows
        self.calls: list[int | None] = []

    async def execute(self, customer_id: int | None) -> list[RequestRow]:
        self.calls.append(customer_id)
        return self.rows


class FakeLoadOrder:
    """Responde `ok` por hp_request_id (default éxito); puede lanzar para uno dado."""

    def __init__(self) -> None:
        self.calls: list[LoadOrderCommand] = []
        self.fail_ids: set[int] = set()
        self.raise_for_id: int | None = None

    async def execute(self, command: LoadOrderCommand):
        self.calls.append(command)
        if command.hp_request_id == self.raise_for_id:
            raise ConnectionError("Canal Directo caído")
        if command.hp_request_id in self.fail_ids:
            return failure("no se pudo")
        return success(f"ORD-{command.hp_request_id}", None)


def _settings(**overrides: str) -> FakeInsumosSettingsRepository:
    repo = FakeInsumosSettingsRepository()
    repo.raw.update(
        {"autoload_enabled": "1", "autoload_max_days": "3", "autoload_min_percent": "15"}
    )
    repo.raw.update(overrides)
    return repo


def _use_case(
    rows: list[RequestRow], settings: FakeInsumosSettingsRepository, max_per_cycle: int = 10
) -> tuple[AutoLoadRequests, FakeListRequests, FakeLoadOrder]:
    list_requests = FakeListRequests(rows)
    load_order = FakeLoadOrder()
    ports = AutoLoadPorts(list_requests=list_requests, load_order=load_order, settings=settings)
    return AutoLoadRequests(ports, max_orders_per_cycle=max_per_cycle), list_requests, load_order


async def test_autoload_deshabilitado_no_hace_nada() -> None:
    use_case, list_requests, load_order = _use_case(
        [_row(1)], _settings(autoload_enabled="0")
    )

    result = await use_case.execute()

    assert (result.considered, result.created, result.skipped) == (0, 0, 0)
    assert list_requests.calls == []  # ni siquiera fetchea — kill switch primero
    assert load_order.calls == []


async def test_elegible_sin_validacion_pendiente_se_carga() -> None:
    use_case, _, load_order = _use_case([_row(1)], _settings())

    result = await use_case.execute()

    assert result.considered == 1
    assert result.created == 1
    assert result.skipped == 0
    assert load_order.calls[0].hp_request_id == 1
    assert load_order.calls[0].dry_run is False
    assert load_order.calls[0].force_override is False


async def test_validacion_pendiente_se_saltea() -> None:
    use_case, _, load_order = _use_case([_row(1, validation_pending=True)], _settings())

    result = await use_case.execute()

    assert result.considered == 0
    assert load_order.calls == []


async def test_ya_cargada_se_saltea() -> None:
    use_case, _, load_order = _use_case([_row(1, order_id="441000-1")], _settings())

    result = await use_case.execute()

    assert result.considered == 0
    assert load_order.calls == []


async def test_zona_con_aviso_de_sucursal_se_saltea() -> None:
    """Se aparta del legacy a propósito: la auto-carga excluye estas solicitudes en vez
    de dejarlas solo con constancia en el Historial, para que no salga un despacho a la
    sucursal equivocada sin que nadie lo vea a tiempo. Quedan para carga manual."""
    use_case, _, load_order = _use_case(
        [_row(1, requiere_cambio_sucursal=True)], _settings()
    )

    result = await use_case.execute()

    assert result.considered == 0
    assert load_order.calls == []


async def test_no_elegible_por_umbral_se_saltea() -> None:
    """days_left/percent_left altos: ninguno de los dos criterios de is_autoload_eligible
    se cumple (max_days=3, min_percent=15 en _settings)."""
    use_case, _, load_order = _use_case(
        [_row(1, days_left=10, percent_left=50.0)], _settings()
    )

    result = await use_case.execute()

    assert result.considered == 0
    assert load_order.calls == []


async def test_sin_percent_left_se_saltea() -> None:
    use_case, _, load_order = _use_case([_row(1, percent_left=None)], _settings())

    result = await use_case.execute()

    assert result.considered == 0
    assert load_order.calls == []


async def test_tope_por_ciclo_corta_el_loop() -> None:
    rows = [_row(i) for i in range(1, 4)]
    use_case, _, load_order = _use_case(rows, _settings(), max_per_cycle=2)

    result = await use_case.execute()

    assert result.created == 2
    assert len(load_order.calls) == 2


async def test_fallo_de_negocio_no_cuenta_pero_sigue_con_el_resto() -> None:
    rows = [_row(1), _row(2)]
    use_case, _, load_order = _use_case(rows, _settings())
    load_order.fail_ids = {1}

    result = await use_case.execute()

    assert result.considered == 2
    assert result.created == 1
    assert result.skipped == 1
    assert [c.hp_request_id for c in load_order.calls] == [1, 2]  # no cortó el loop


async def test_excepcion_inesperada_no_corta_el_ciclo() -> None:
    """Un fallo de red/bug puntual en una fila no debe tirar abajo el resto del
    ciclo (mismo criterio best-effort que el legacy)."""
    rows = [_row(1), _row(2)]
    use_case, _, load_order = _use_case(rows, _settings())
    load_order.raise_for_id = 1

    result = await use_case.execute()

    assert result.created == 1  # solo la fila 2 se cargó
    assert [c.hp_request_id for c in load_order.calls] == [1, 2]
