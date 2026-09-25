"""Períodos mensuales "AAAA-MM" y rangos de meses del reporte.

Mismo formato que el legacy (el `fecha` ISO de cada incidente empieza con su
período, y así se filtra). Distinto del `Periodo` AAAAMM entero de sla: son
módulos independientes y cada uno conserva el formato de su fuente."""

import re
from dataclasses import dataclass
from datetime import date

from src.modules.reporte_incidentes.domain.errors import PeriodoInvalidoError

MESES = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
)
# Rango máximo pedible de una vez: cada mes viejo agranda el `Top` del SOAP.
MAX_MESES_RANGO = 24
_FORMATO = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


@dataclass(frozen=True, slots=True, order=True)
class Periodo:
    anio: int
    mes: int

    @classmethod
    def parse(cls, raw: str) -> "Periodo":
        match = _FORMATO.match(raw.strip())
        if match is None:
            raise PeriodoInvalidoError(raw)
        return cls(int(match.group(1)), int(match.group(2)))

    @classmethod
    def de_fecha(cls, dia: date) -> "Periodo":
        return cls(dia.year, dia.month)

    def __str__(self) -> str:
        return f"{self.anio:04d}-{self.mes:02d}"

    @property
    def etiqueta(self) -> str:
        return f"{MESES[self.mes - 1]} {self.anio}"

    def menos(self, meses: int) -> "Periodo":
        indice = self.anio * 12 + (self.mes - 1) - meses
        return Periodo(indice // 12, indice % 12 + 1)


def meses_entre(desde: Periodo, hasta: Periodo) -> int:
    """Cantidad de meses entre dos períodos, inclusive (asume desde <= hasta)."""
    return hasta.anio * 12 + hasta.mes - (desde.anio * 12 + desde.mes) + 1


def rango_periodos(hasta: Periodo, meses: int) -> list[Periodo]:
    """Los `meses` períodos que terminan en `hasta`, del más viejo al más nuevo."""
    return [hasta.menos(i) for i in range(max(meses, 1) - 1, -1, -1)]


def periodos_recientes(cantidad: int, hoy: date) -> list[Periodo]:
    """Los últimos `cantidad` períodos hasta el mes de `hoy`, del más nuevo al más viejo."""
    actual = Periodo.de_fecha(hoy)
    return [actual.menos(i) for i in range(cantidad)]


def etiqueta_rango(hasta: Periodo, meses: int) -> str:
    """"Septiembre 2026" o "Abril 2026 – Septiembre 2026"."""
    if meses <= 1:
        return hasta.etiqueta
    return f"{hasta.menos(meses - 1).etiqueta} – {hasta.etiqueta}"


def acotar_meses(meses: int | None) -> int:
    """El legacy clampea el `months` de la URL a [1, 24]; inválido => 1."""
    if meses is None or meses < 1:
        return 1
    return min(meses, MAX_MESES_RANGO)
