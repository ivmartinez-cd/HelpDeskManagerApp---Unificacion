import uuid
from datetime import date

from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.contadores.domain.services.operador_efectivo import resolver_operador_efectivo

_AUSENTE = "mjvela"
_REEMPLAZANTE = "vipaez"
_CLIENTE = "NEUMATICOS ROSMI SRL"
_OTRO_CLIENTE = "OTRO CLIENTE SA"


def _override(**overrides: object) -> AsignacionOverride:
    base = {
        "id": uuid.uuid4(),
        "operador_ausente_id": _AUSENTE,
        "operador_reemplazante_id": _REEMPLAZANTE,
        "vigente_desde": date(2026, 8, 1),
        "vigente_hasta": date(2026, 8, 15),
        "alcance": "TOTAL",
        "estado": "ACTIVA",
        "motivo": None,
        "created_by_user_id": uuid.uuid4(),
    }
    base.update(overrides)
    return AsignacionOverride(**base)  # type: ignore[arg-type]


def test_sin_overrides_devuelve_el_operador_original() -> None:
    resultado = resolver_operador_efectivo(_AUSENTE, _CLIENTE, date(2026, 8, 5), [])
    assert resultado == _AUSENTE


def test_override_total_vigente_devuelve_el_reemplazante() -> None:
    override = _override()
    resultado = resolver_operador_efectivo(_AUSENTE, _CLIENTE, date(2026, 8, 5), [override])
    assert resultado == _REEMPLAZANTE


def test_override_fuera_de_rango_no_aplica() -> None:
    override = _override()
    resultado = resolver_operador_efectivo(_AUSENTE, _CLIENTE, date(2026, 9, 1), [override])
    assert resultado == _AUSENTE


def test_override_cancelado_no_aplica() -> None:
    override = _override(estado="CANCELADA")
    resultado = resolver_operador_efectivo(_AUSENTE, _CLIENTE, date(2026, 8, 5), [override])
    assert resultado == _AUSENTE


def test_override_por_cliente_puntual_solo_aplica_a_ese_cliente() -> None:
    override = _override(alcance=frozenset({_CLIENTE}))

    assert (
        resolver_operador_efectivo(_AUSENTE, _CLIENTE, date(2026, 8, 5), [override])
        == _REEMPLAZANTE
    )
    assert (
        resolver_operador_efectivo(_AUSENTE, _OTRO_CLIENTE, date(2026, 8, 5), [override])
        == _AUSENTE
    )


def test_cliente_none_no_matchea_alcance_puntual() -> None:
    override = _override(alcance=frozenset({_CLIENTE}))
    resultado = resolver_operador_efectivo(_AUSENTE, None, date(2026, 8, 5), [override])
    assert resultado == _AUSENTE


def test_operador_original_none_devuelve_none() -> None:
    assert resolver_operador_efectivo(None, _CLIENTE, date(2026, 8, 5), []) is None
