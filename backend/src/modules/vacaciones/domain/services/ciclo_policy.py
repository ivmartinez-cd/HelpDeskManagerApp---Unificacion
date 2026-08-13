"""Apertura de ciclos, evaluada lazy (D7 del plan — sin background jobs).

Paridad con `ensureCycle`/`autoOpenCyclesIfNeeded` del legacy: el ciclo del
año en curso está siempre abierto; el del año siguiente se abre cuando la
fecha actual alcanza el día/mes configurado (inclusive); cualquier otro año
está cerrado. El flag `is_open` almacenado prevalece si ya es True (apertura
forzada manual). `allow_advance_request` NO participa acá: se valida al crear
la solicitud, igual que en el legacy.
"""

from datetime import date

from src.modules.vacaciones.domain.value_objects.config_vacaciones import ConfigVacaciones


def fecha_apertura_proximo_ciclo(hoy: date, config: ConfigVacaciones) -> date:
    return date(hoy.year, config.next_year_open_month, config.next_year_open_day)


def is_open_por_politica(year: int, hoy: date, config: ConfigVacaciones) -> bool:
    if year == hoy.year:
        return True
    if year == hoy.year + 1:
        return hoy >= fecha_apertura_proximo_ciclo(hoy, config)
    return False


def apertura_efectiva(
    is_open_almacenado: bool, year: int, hoy: date, config: ConfigVacaciones
) -> bool:
    return is_open_almacenado or is_open_por_politica(year, hoy, config)
