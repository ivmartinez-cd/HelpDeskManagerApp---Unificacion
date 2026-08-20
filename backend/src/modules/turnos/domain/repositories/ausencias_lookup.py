import uuid
from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AusenciaAprobada:
    user_id: uuid.UUID
    desde: date
    hasta: date


class AusenciasLookup(Protocol):
    """Puerto inverso vacaciones → turnos (ADR-025): vacaciones APROBADAS de
    usuarios de la plataforma que intersectan un rango, para advertir en el
    editor de grilla variante si un cubriente va a estar ausente. Implementado
    en infrastructure leyendo las tablas de vacaciones -- el contrato
    `turnos-domain-app-independent-from-vacaciones` prohíbe importarlas acá."""

    async def ausencias_aprobadas_en(
        self, user_ids: list[uuid.UUID], desde: date, hasta: date
    ) -> list[AusenciaAprobada]: ...


class AusenciasLookupNulo:
    """Implementación vacía para wiring sin vacaciones (tests, scripts)."""

    async def ausencias_aprobadas_en(
        self, user_ids: list[uuid.UUID], desde: date, hasta: date
    ) -> list[AusenciaAprobada]:
        return []
