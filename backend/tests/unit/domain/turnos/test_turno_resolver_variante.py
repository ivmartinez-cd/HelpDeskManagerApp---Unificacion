"""TurnoResolver con grilla variante (modo vacaciones, ADR-025)."""

import uuid
from datetime import date, time

from src.modules.turnos.domain.services.turno_resolver import TurnoResolver
from src.shared.domain.value_objects.asignacion_override import AsignacionOverride
from tests.unit.domain.turnos.caso_majo import (
    LUNES_VUELTA,
    MIERCOLES_DENTRO,
    MIERCOLES_SIGUIENTE,
    CasoMajo,
)


def _resolver(caso: CasoMajo, fecha: date, **kwargs: object) -> list[tuple[str, str, str, list]]:
    results = TurnoResolver().resolve_shifts(
        casillas=caso.casillas,
        slots=caso.slots,
        asignaciones=caso.asignaciones,
        target_date=fecha,
        target_time=time(10, 0),
        **kwargs,  # type: ignore[arg-type]
    )
    return [
        (
            r.casilla_nombre,
            r.hora_inicio.strftime("%H:%M"),
            r.hora_fin.strftime("%H:%M"),
            r.user_ids,
        )
        for r in results
    ]


def _titular_esperada(caso: CasoMajo) -> list[tuple[str, str, str, list]]:
    return [
        ("INSUMOS", "08:00", "11:00", [caso.majo]),
        ("INSUMOS", "11:00", "13:00", [caso.luna]),
        ("INSUMOS", "13:00", "17:00", [caso.mariano]),
        ("INSUMOS", "17:00", "18:00", [caso.victor]),
        ("ST", "09:00", "13:00", [caso.victor]),
        ("ST", "13:00", "15:00", [caso.majo]),
        ("ST", "15:00", "18:00", [caso.luna]),
    ]


def _variante_esperada(caso: CasoMajo) -> list[tuple[str, str, str, list]]:
    return [
        ("INSUMOS", "08:30", "11:00", [caso.mariano]),
        ("INSUMOS", "11:00", "13:00", [caso.luna]),
        ("INSUMOS", "13:00", "17:00", [caso.mariano]),
        ("INSUMOS", "17:00", "18:00", [caso.victor]),
        ("ST", "08:00", "09:00", [caso.mariana]),
        ("ST", "09:00", "14:00", [caso.victor]),
        ("ST", "14:00", "18:00", [caso.luna]),
    ]


def test_con_variante_vigente_las_franjas_salen_de_la_variante() -> None:
    caso = CasoMajo()
    variante = caso.variante_esperada()

    assert _resolver(caso, MIERCOLES_DENTRO, variante=variante) == _variante_esperada(caso)


def test_sin_variante_se_resuelve_la_grilla_titular() -> None:
    caso = CasoMajo()

    assert _resolver(caso, MIERCOLES_DENTRO) == _titular_esperada(caso)


def test_variante_vencida_vuelve_a_la_titular_sin_accion() -> None:
    caso = CasoMajo()
    variante = caso.variante_esperada()

    assert _resolver(caso, MIERCOLES_SIGUIENTE, variante=variante) == _titular_esperada(caso)
    assert _resolver(caso, LUNES_VUELTA, variante=variante) == _titular_esperada(caso)


def test_variante_cancelada_no_aplica_aunque_la_fecha_este_en_vigencia() -> None:
    caso = CasoMajo()
    variante = caso.variante_esperada()
    variante.estado = "CANCELADA"

    assert _resolver(caso, MIERCOLES_DENTRO, variante=variante) == _titular_esperada(caso)


def test_override_total_sigue_aplicando_sobre_la_variante() -> None:
    caso = CasoMajo()
    variante = caso.variante_esperada()
    pedro = uuid.uuid4()
    cobertura: AsignacionOverride[uuid.UUID, uuid.UUID] = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=caso.luna,
        operador_reemplazante_id=pedro,
        desde=date(2026, 8, 26),
        hasta=date(2026, 8, 26),
        alcance="TOTAL",
        estado="ACTIVA",
        motivo=None,
        created_by_user_id=uuid.uuid4(),
    )

    resultado = _resolver(
        caso, MIERCOLES_DENTRO, variante=variante, overrides_por_ausente={caso.luna: [cobertura]}
    )

    assert ("INSUMOS", "11:00", "13:00", [pedro]) in resultado
    assert ("ST", "14:00", "18:00", [pedro]) in resultado


def test_override_parcial_sobre_slot_titular_no_aplica_a_la_variante() -> None:
    """Asimetría documentada en ADR-025: el alcance parcial referencia
    `turno_slot.id` titulares y las franjas de la variante tienen ids propios."""
    caso = CasoMajo()
    variante = caso.variante_esperada()
    pedro = uuid.uuid4()
    slot_titular_luna = next(
        a.slot_id for a in caso.asignaciones if a.user_id == caso.luna
    )
    cobertura: AsignacionOverride[uuid.UUID, uuid.UUID] = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=caso.luna,
        operador_reemplazante_id=pedro,
        desde=date(2026, 8, 24),
        hasta=date(2026, 8, 28),
        alcance=frozenset({slot_titular_luna}),
        estado="ACTIVA",
        motivo=None,
        created_by_user_id=uuid.uuid4(),
    )

    resultado = _resolver(
        caso, MIERCOLES_DENTRO, variante=variante, overrides_por_ausente={caso.luna: [cobertura]}
    )

    assert resultado == _variante_esperada(caso)
