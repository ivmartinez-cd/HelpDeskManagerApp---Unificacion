"""El resolver de ADR-013 es genérico sobre el tipo de id de operador/alcance
-- contadores usa `str` (usernames de Gestión), prestadores/turnos usan
`uuid.UUID`. Estos tests corren la misma batería de casos con ambos tipos
para confirmar que la genericidad funciona en la práctica, no solo en el
type-checker."""

import uuid
from datetime import date

import pytest

from src.shared.domain.services.asignacion_override_resolver import (
    hay_solapamiento,
    resolver_operador_efectivo,
    resolver_override_aplicable,
)
from src.shared.domain.value_objects.asignacion_override import AsignacionOverride


def _override(
    ausente: object,
    reemplazante: object,
    *,
    desde: date,
    hasta: date,
    alcance: object,
    estado: str = "ACTIVA",
) -> AsignacionOverride:
    return AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=ausente,
        operador_reemplazante_id=reemplazante,
        desde=desde,
        hasta=hasta,
        alcance=alcance,
        estado=estado,
        motivo=None,
        created_by_user_id=uuid.uuid4(),
    )


@pytest.mark.parametrize(
    ("ausente", "reemplazante", "criterio"),
    [
        (uuid.uuid4(), uuid.uuid4(), uuid.uuid4()),
        ("mjvela", "ltorres", "Cliente ACME"),
    ],
    ids=["uuid", "str"],
)
def test_resuelve_al_reemplazante_con_override_total(
    ausente: object, reemplazante: object, criterio: object
) -> None:
    override = _override(
        ausente, reemplazante, desde=date(2026, 8, 1), hasta=date(2026, 8, 15), alcance="TOTAL"
    )

    assert (
        resolver_operador_efectivo(ausente, criterio, date(2026, 8, 10), [override])
        == reemplazante
    )


@pytest.mark.parametrize(
    ("ausente", "reemplazante", "criterio", "otro_criterio"),
    [
        (uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()),
        ("mjvela", "ltorres", "Cliente ACME", "Cliente Otro"),
    ],
    ids=["uuid", "str"],
)
def test_alcance_parcial_solo_matchea_el_criterio_incluido(
    ausente: object, reemplazante: object, criterio: object, otro_criterio: object
) -> None:
    override = _override(
        ausente,
        reemplazante,
        desde=date(2026, 8, 1),
        hasta=date(2026, 8, 15),
        alcance=frozenset({criterio}),
    )

    assert (
        resolver_operador_efectivo(ausente, criterio, date(2026, 8, 10), [override])
        == reemplazante
    )
    assert (
        resolver_operador_efectivo(ausente, otro_criterio, date(2026, 8, 10), [override])
        == ausente
    )


def test_fuera_de_vigencia_devuelve_el_original() -> None:
    ausente, reemplazante, criterio = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    override = _override(
        ausente, reemplazante, desde=date(2026, 8, 1), hasta=date(2026, 8, 15), alcance="TOTAL"
    )

    assert (
        resolver_operador_efectivo(ausente, criterio, date(2026, 9, 1), [override]) == ausente
    )


def test_override_cancelado_no_aplica() -> None:
    ausente, reemplazante, criterio = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    override = _override(
        ausente,
        reemplazante,
        desde=date(2026, 8, 1),
        hasta=date(2026, 8, 15),
        alcance="TOTAL",
        estado="CANCELADA",
    )

    assert resolver_override_aplicable(ausente, criterio, date(2026, 8, 10), [override]) is None


def test_operador_original_none_devuelve_none() -> None:
    assert resolver_operador_efectivo(None, uuid.uuid4(), date(2026, 8, 10), []) is None


def test_criterio_alcance_none_solo_matchea_total() -> None:
    ausente, reemplazante = uuid.uuid4(), uuid.uuid4()
    parcial = _override(
        ausente,
        reemplazante,
        desde=date(2026, 8, 1),
        hasta=date(2026, 8, 15),
        alcance=frozenset({uuid.uuid4()}),
    )
    total = _override(
        ausente, reemplazante, desde=date(2026, 8, 1), hasta=date(2026, 8, 15), alcance="TOTAL"
    )

    assert resolver_operador_efectivo(ausente, None, date(2026, 8, 10), [parcial]) == ausente
    assert (
        resolver_operador_efectivo(ausente, None, date(2026, 8, 10), [total]) == reemplazante
    )


def test_hay_solapamiento_detecta_fechas_y_alcance_en_comun() -> None:
    existente = _override(
        uuid.uuid4(), uuid.uuid4(), desde=date(2026, 8, 1), hasta=date(2026, 8, 15), alcance="TOTAL"
    )

    assert hay_solapamiento(date(2026, 8, 10), date(2026, 8, 20), "TOTAL", [existente]) is True
    assert hay_solapamiento(date(2026, 9, 1), date(2026, 9, 10), "TOTAL", [existente]) is False
