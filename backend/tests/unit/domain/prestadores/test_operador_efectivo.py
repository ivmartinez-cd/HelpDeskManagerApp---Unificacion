import uuid
from datetime import date

from src.modules.prestadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.prestadores.domain.services.operador_efectivo import resolver_operador_efectivo

_AUSENTE = uuid.uuid4()
_REEMPLAZANTE = uuid.uuid4()
_PRESTADOR = uuid.uuid4()
_OTRO_PRESTADOR = uuid.uuid4()


def _override(**overrides: object) -> AsignacionOverride:
    base = {
        "id": uuid.uuid4(),
        "operador_ausente_id": _AUSENTE,
        "operador_reemplazante_id": _REEMPLAZANTE,
        "desde": date(2026, 8, 1),
        "hasta": date(2026, 8, 15),
        "alcance": "TOTAL",
        "estado": "ACTIVA",
        "motivo": None,
        "created_by_user_id": uuid.uuid4(),
    }
    base.update(overrides)
    return AsignacionOverride(**base)  # type: ignore[arg-type]


def test_sin_overrides_devuelve_el_operador_original() -> None:
    resultado = resolver_operador_efectivo(_AUSENTE, _PRESTADOR, date(2026, 8, 5), [])
    assert resultado == _AUSENTE


def test_override_total_vigente_devuelve_el_reemplazante() -> None:
    override = _override()
    resultado = resolver_operador_efectivo(_AUSENTE, _PRESTADOR, date(2026, 8, 5), [override])
    assert resultado == _REEMPLAZANTE


def test_override_fuera_de_rango_no_aplica() -> None:
    override = _override()
    resultado = resolver_operador_efectivo(_AUSENTE, _PRESTADOR, date(2026, 9, 1), [override])
    assert resultado == _AUSENTE


def test_override_cancelado_no_aplica() -> None:
    override = _override(estado="CANCELADA")
    resultado = resolver_operador_efectivo(_AUSENTE, _PRESTADOR, date(2026, 8, 5), [override])
    assert resultado == _AUSENTE


def test_override_por_prestador_puntual_solo_aplica_a_ese_prestador() -> None:
    override = _override(alcance=frozenset({_PRESTADOR}))

    assert (
        resolver_operador_efectivo(_AUSENTE, _PRESTADOR, date(2026, 8, 5), [override])
        == _REEMPLAZANTE
    )
    assert (
        resolver_operador_efectivo(_AUSENTE, _OTRO_PRESTADOR, date(2026, 8, 5), [override])
        == _AUSENTE
    )


def test_operador_original_none_devuelve_none() -> None:
    assert resolver_operador_efectivo(None, _PRESTADOR, date(2026, 8, 5), []) is None
