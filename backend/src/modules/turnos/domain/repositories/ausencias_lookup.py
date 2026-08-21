import uuid
from dataclasses import dataclass
from datetime import date, time
from typing import Protocol

TIPO_VACACIONES = "VACACIONES"
TIPO_HOME_OFFICE = "HOME_OFFICE"
TIPO_CAMBIO_HORARIO = "CAMBIO_HORARIO"


@dataclass(frozen=True, slots=True)
class AusenciaAprobada:
    """Novedad APROBADA de un usuario de la plataforma que intersecta un rango:
    vacaciones o una baja (enfermedad, trámite, home office, cambio de
    horario…). `tipo` es el código de origen; `hora_desde`/`hora_hasta` solo
    vienen en CAMBIO_HORARIO (el operador trabaja, pero en otra ventana)."""

    user_id: uuid.UUID
    desde: date
    hasta: date
    tipo: str = TIPO_VACACIONES
    hora_desde: time | None = None
    hora_hasta: time | None = None

    @property
    def impide_cobertura(self) -> bool:
        """Home office no saca al operador de la grilla; un cambio de horario
        la afecta solo parcialmente (se advierte, no se trata como ausencia)."""
        return self.tipo != TIPO_HOME_OFFICE

    @property
    def detalle(self) -> str:
        """Texto corto para avisos/badges: 'Vacaciones', 'Home office',
        'Horario 08:00–17:00', 'Baja por enfermedad'…"""
        if self.tipo == TIPO_CAMBIO_HORARIO and self.hora_desde and self.hora_hasta:
            return f"Horario {self.hora_desde:%H:%M}–{self.hora_hasta:%H:%M}"
        return _DETALLES.get(self.tipo, self.tipo.replace("_", " ").capitalize())


_DETALLES = {
    TIPO_VACACIONES: "Vacaciones",
    TIPO_HOME_OFFICE: "Home office",
    "BAJA_ENFERMEDAD": "Baja por enfermedad",
    "TRAMITE_PERSONAL": "Trámite personal",
    "DESCUENTO_DIA": "Día de descuento",
    "GUARDIA": "Guardia",
    "DIA_ESTUDIO": "Día de estudio",
    "OTHER": "Ausencia",
}


class AusenciasLookup(Protocol):
    """Puerto inverso vacaciones → turnos (ADR-025): vacaciones y bajas
    APROBADAS de usuarios de la plataforma que intersectan un rango, para
    advertir en el editor de grilla variante y anotar Turnos del día.
    Implementado en infrastructure leyendo las tablas de vacaciones -- el
    contrato `turnos-domain-app-independent-from-vacaciones` prohíbe
    importarlas acá."""

    async def ausencias_aprobadas_en(
        self, user_ids: list[uuid.UUID], desde: date, hasta: date
    ) -> list[AusenciaAprobada]: ...


class AusenciasLookupNulo:
    """Implementación vacía para wiring sin vacaciones (tests, scripts)."""

    async def ausencias_aprobadas_en(
        self, user_ids: list[uuid.UUID], desde: date, hasta: date
    ) -> list[AusenciaAprobada]:
        return []
