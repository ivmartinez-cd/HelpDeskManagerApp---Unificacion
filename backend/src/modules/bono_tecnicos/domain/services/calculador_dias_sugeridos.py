"""Sugerencia de "Días" a partir de asistencias de Gestión de Personal —
decisión de negocio confirmada con el usuario (2026-08-24, ver memoria de
proyecto `project-bono-tecnicos-analisis`): "días hábiles simples" = lunes a
viernes del período, sin restar feriados ni mirar el turno propio del
técnico, menos los tipos de ausencia que efectivamente significan que no
trabajó ese día (DESCUENTO_DIA, BAJA_ENFERMEDAD, TRAMITE_PERSONAL,
DIA_ESTUDIO — confirmado explícitamente; GUARDIA/HOME_OFFICE/CAMBIO_HORARIO/
OTHER no restan, la selección de tipos vive en el gateway de infraestructura).

Es solo una sugerencia editable: `bono_tecnico_input.dias` sigue siendo el
valor que manda, cargado/confirmado a mano (ver `calculador_puntaje.py`) —
esto nunca escribe ahí solo."""

from dataclasses import dataclass
from datetime import date, timedelta

from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo

_SABADO = 5  # date.weekday(): lunes=0 ... domingo=6


@dataclass(frozen=True, slots=True)
class AusenciaTecnico:
    """Proyección mínima de una `Ausencia` de vacaciones — no la entidad
    completa, para no acoplar el dominio de bono_tecnicos al de vacaciones
    (el cruce vive en infrastructure)."""

    start_date: date
    end_date: date
    half_day: bool

    def cubre(self, dia: date) -> bool:
        return self.start_date <= dia <= self.end_date


def _dias_habiles(periodo: Periodo) -> list[date]:
    dias = []
    dia = periodo.primer_dia
    while dia <= periodo.ultimo_dia:
        if dia.weekday() < _SABADO:
            dias.append(dia)
        dia += timedelta(days=1)
    return dias


def calcular_dias_sugeridos(periodo: Periodo, ausencias: list[AusenciaTecnico]) -> int:
    habiles = _dias_habiles(periodo)
    descontados = 0.0
    for dia in habiles:
        match = next((a for a in ausencias if a.cubre(dia)), None)
        if match is not None:
            descontados += 0.5 if match.half_day else 1.0
    return max(0, round(len(habiles) - descontados))
