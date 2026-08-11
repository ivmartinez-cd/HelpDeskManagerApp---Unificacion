"""Tests de ValidationDiagnosis — port de test_validation_diagnosis.py del legacy más
los casos de swap/multicanal/antecedente que allá vivían en test_request_validation.py.

Casos reales: PHC5R18423 (cambio de cartucho + ST técnico cerrado horas antes) y
CN4766M07W (glitch multicanal con antecedente de caída-y-recuperación)."""

from src.modules.insumos.domain.services.validation_diagnosis import ValidationDiagnosis
from src.modules.insumos.domain.value_objects.cd_supply import CdIncident, CdMachine
from tests.unit.domain.insumos.fakes import FakeInsightGateway, FakeWsAycGateway

REQ = {
    "id": 975078,
    "requested": "2026-08-04T19:24:09.000Z",
    "consumable": {"sku": "CF287X", "percentLeft": 0, "index": 1, "serialNumber": "16849576"},
}

MACHINE = CdMachine(familia_id="255", machine_id="51497")

CLOSED_INCIDENT_RECIENTE = CdIncident(
    numero="841863",
    estado="Cerrado",
    fecha_cierre="04/08/2026 13:42:00",  # 2.7hs antes de REQ["requested"] (16:42Z vs 19:24Z)
    tecnico="CD - Ignacio SIGUEN",
)


def _req_sin_swap(base: dict | None = None) -> dict:
    """REQ sin serialNumber, para que no dispare swap_note y otra señal quede sola."""
    base = base or REQ
    return {**base, "consumable": {**base["consumable"], "serialNumber": ""}}


def _diagnosis(insight: FakeInsightGateway, wsayc: FakeWsAycGateway) -> ValidationDiagnosis:
    return ValidationDiagnosis(insight, wsayc)  # type: ignore[arg-type]


def _world() -> tuple[FakeInsightGateway, FakeWsAycGateway]:
    insight = FakeInsightGateway()
    wsayc = FakeWsAycGateway()
    wsayc.machine = MACHINE
    return insight, wsayc


async def test_detecta_cambio_de_insumo_cuando_el_chip_fisico_cambio() -> None:
    """Caso real PHC5R18423: la serie del chip cambió respecto a la última lectura —
    swap_note enmascara el serial completo pero deja los últimos 4 dígitos."""
    insight, wsayc = _world()
    insight.history_by_device[244045] = [{"consumableSerial": "16845083", "level": 84}]

    diagnosis = await _diagnosis(insight, wsayc).build(244045, REQ, device_serial="PHC5R18423")

    assert diagnosis is not None
    assert diagnosis.headline == "Posible cambio de cartucho"
    assert diagnosis.swap_note is not None
    assert "16845083" not in diagnosis.swap_note
    assert "5083" in diagnosis.swap_note
    assert "84%" in diagnosis.swap_note


async def test_sin_cambio_de_chip_no_hay_swap_note() -> None:
    insight, wsayc = _world()
    insight.history_by_device[244045] = [{"consumableSerial": "16849576", "level": 40}]

    diagnosis = await _diagnosis(insight, wsayc).build(244045, REQ, device_serial="PHC5R18423")

    assert diagnosis is not None
    assert diagnosis.swap_note is None


DIAG_REQUEST = {
    "id": 975600,
    "requested": "2026-08-05T11:12:59.000Z",
    "consumable": {"sku": "498M7A", "percentLeft": 0, "index": 2, "serialNumber": ""},
}

# Datos reales del equipo CN4766M07W: cian cayó a 0% y se recuperó a 20% el 24/jul.
DIAG_HISTORY = [
    {"recordDate": "2026-07-24T18:47:05.190Z", "level": 20, "engineCycles": 24},
    {"recordDate": "2026-07-24T15:27:31.860Z", "level": 0, "engineCycles": 24},
]


async def test_diagnostico_detecta_glitch_multicanal_en_curso() -> None:
    """OTRO consumible del mismo equipo también casi en 0% ahora mismo: la señal más
    fuerte después del swap — tiene prioridad sobre el antecedente."""
    insight, wsayc = _world()
    insight.history_by_device[240233] = DIAG_HISTORY
    insight.consumables_by_device[240233] = [
        {"sku": "498M7A", "percentLeft": 0, "index": 2},
        {"sku": "4J6Y6A", "percentLeft": 0, "index": 3, "colour": "MAGENTA"},
    ]

    diagnosis = await _diagnosis(insight, wsayc).build(
        240233, DIAG_REQUEST, device_serial="CN4766M07W"
    )

    assert diagnosis is not None
    assert diagnosis.headline == "Glitch de sensor (multicanal, en curso)"
    assert "MAGENTA" in diagnosis.detail


async def test_diagnostico_detecta_antecedente_sin_multicanal_ahora() -> None:
    """Sin otro canal caído ahora, pero con caída-y-recuperación previa en el propio
    historial: headline de antecedente, fechas en hora Argentina."""
    insight, wsayc = _world()
    insight.history_by_device[240233] = DIAG_HISTORY
    insight.consumables_by_device[240233] = [
        {"sku": "498M7A", "percentLeft": 0, "index": 2},
        {"sku": "4J6Y6A", "percentLeft": 30, "index": 3, "colour": "MAGENTA"},
    ]

    diagnosis = await _diagnosis(insight, wsayc).build(
        240233, DIAG_REQUEST, device_serial="CN4766M07W"
    )

    assert diagnosis is not None
    assert diagnosis.headline == "Glitch de sensor (antecedente en este equipo)"
    # 18:47 UTC y 15:27 UTC del 24/jul -> 15:47 y 12:27 hora Argentina (UTC-3).
    assert "24/07 15:47" in diagnosis.detail
    assert "24/07 12:27" in diagnosis.detail
    assert "contador de ciclos de motor no cambió" in diagnosis.detail


async def test_diagnostico_sin_evidencia_no_inventa_una_conclusion() -> None:
    insight, wsayc = _world()
    wsayc.machine = None  # tampoco hay ST que encontrar

    diagnosis = await _diagnosis(insight, wsayc).build(
        240233, DIAG_REQUEST, device_serial="CN4766M07W"
    )

    assert diagnosis is not None
    assert diagnosis.headline == "Sin antecedentes claros — validar manualmente"
    assert "podría ser una depleción real" in diagnosis.detail


async def test_st_reciente_se_agrega_al_detalle_sin_cambiar_headline_de_swap() -> None:
    """El swap sigue siendo la señal más fuerte, pero el ST cerrado horas antes se
    agrega como evidencia corroborante en el detalle — caso real PHC5R18423."""
    insight, wsayc = _world()
    insight.history_by_device[244045] = [{"consumableSerial": "16845083", "level": 84}]
    wsayc.machine_incidents = [CLOSED_INCIDENT_RECIENTE]

    diagnosis = await _diagnosis(insight, wsayc).build(244045, REQ, device_serial="PHC5R18423")

    assert diagnosis is not None
    assert diagnosis.headline == "Posible cambio de cartucho"
    assert "ST técnico (#841863)" in diagnosis.detail
    assert "Ignacio SIGUEN" in diagnosis.detail


async def test_st_reciente_sin_otra_senal_es_su_propio_headline() -> None:
    insight, wsayc = _world()
    wsayc.machine_incidents = [CLOSED_INCIDENT_RECIENTE]

    diagnosis = await _diagnosis(insight, wsayc).build(
        244045, _req_sin_swap(), device_serial="PHC5R18423"
    )

    assert diagnosis is not None
    assert diagnosis.headline == "Intervención técnica reciente registrada"


async def test_st_abierto_se_marca_en_curso() -> None:
    insight, wsayc = _world()
    wsayc.machine_incidents = [
        CdIncident(numero="841863", estado="En Curso", tecnico="CD - Ignacio SIGUEN")
    ]

    diagnosis = await _diagnosis(insight, wsayc).build(
        244045, _req_sin_swap(), device_serial="PHC5R18423"
    )

    assert diagnosis is not None
    assert "todavía en curso" in diagnosis.detail


async def test_st_cerrado_hace_demasiado_no_se_menciona() -> None:
    """Un ST cerrado hace semanas no tiene que ver con la solicitud de ahora."""
    insight, wsayc = _world()
    wsayc.machine_incidents = [
        CdIncident(numero="841863", estado="Cerrado", fecha_cierre="01/07/2026 10:00:00")
    ]

    diagnosis = await _diagnosis(insight, wsayc).build(
        244045, _req_sin_swap(), device_serial="PHC5R18423"
    )

    assert diagnosis is not None
    assert diagnosis.headline == "Sin antecedentes claros — validar manualmente"
    assert "ST técnico" not in diagnosis.detail


async def test_sin_maquina_en_canal_directo_no_rompe() -> None:
    insight, wsayc = _world()
    wsayc.machine = None

    diagnosis = await _diagnosis(insight, wsayc).build(
        244045, _req_sin_swap(), device_serial="EQUIPO-SIN-CD"
    )

    assert diagnosis is not None
    assert diagnosis.headline == "Sin antecedentes claros — validar manualmente"


async def test_excepcion_consultando_canal_directo_no_rompe() -> None:
    """Best-effort: un problema de red/WSDL con CD no tira abajo el diagnóstico."""
    insight, wsayc = _world()
    wsayc.machine_error = RuntimeError("wsAyC caído")

    diagnosis = await _diagnosis(insight, wsayc).build(
        244045, _req_sin_swap(), device_serial="PHC5R18423"
    )

    assert diagnosis is not None
    assert diagnosis.headline == "Sin antecedentes claros — validar manualmente"


async def test_sin_index_no_hay_diagnostico() -> None:
    insight, wsayc = _world()
    sin_index = {**REQ, "consumable": {"sku": "CF287X", "percentLeft": 0}}

    assert await _diagnosis(insight, wsayc).build(244045, sin_index) is None


async def test_error_consultando_historial_no_arma_diagnostico() -> None:
    """Sin historial no hay diagnóstico (None) — la ventana de validación arranca
    igual, solo que sin anotación (es informativa, no una decisión)."""
    insight, wsayc = _world()
    insight.history_error = RuntimeError("Insight caído")

    assert await _diagnosis(insight, wsayc).build(244045, REQ) is None
