"""Planificación pura del sync de tarifarios desde Siges (ADR-014, dataset 2).

Pivot wide→long de `CostoServicio` + resolución de SPST + plan de acciones:
- crear: la vigencia (tipo, spst_id, vigencia_desde) no existe localmente.
- conflicto: existe pero con costo distinto — se reporta, NUNCA se escribe.
- sin_cambios: existe con los mismos costos (tolerancia 0.01, la de ALT001).
Descripciones sin mapeo a un SPST quedan fuera del plan y se reportan aparte.
Hasta 2026-09 el destino de este mapeo era una "zona" de texto; es un SPST real
desde el refactor `Tarifario.zona` → `Tarifario.spst_id` (ver esa entidad)."""

import uuid
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.entities.tarifario import (
    TIPO_CORRECTIVO,
    TIPO_GUARDIA,
    TIPO_INSTALACION_DESINSTALACION,
    TIPO_PRE_CORRECTIVO,
    TIPO_PREVENTIVO,
    TIPO_SISTEMAS,
    Tarifario,
)
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCostoServicio,
)
from src.modules.liquidaciones.domain.services.vinculacion_siges import (
    nombres_compatibles,
    normalizar_nombre,
)

TOLERANCIA_COSTO = 0.01
_GENERICA = "generica"
_DESCRIPCIONES_EXCLUIDAS = {"de baja", "sin servicio"}

# (tipo_servicio local, atributo del VO wide de Siges)
_TIPOS: tuple[tuple[str, str], ...] = (
    (TIPO_CORRECTIVO, "correctivo"),
    (TIPO_PREVENTIVO, "preventivo"),
    (TIPO_INSTALACION_DESINSTALACION, "instalacion"),
    (TIPO_PRE_CORRECTIVO, "pre_correctivo"),
    (TIPO_GUARDIA, "guardia"),
    (TIPO_SISTEMAS, "sistemas"),
)


@dataclass(frozen=True)
class TarifaCandidata:
    tipo_servicio: str
    spst_id: uuid.UUID | None
    costo_servicio: float
    costo_km: float
    vigencia_desde: date


@dataclass(frozen=True)
class ConflictoTarifa:
    tipo_servicio: str
    spst_id: uuid.UUID | None
    vigencia_desde: date
    campo: str
    valor_local: float
    valor_siges: float


@dataclass(frozen=True)
class PlanSyncTarifarios:
    a_crear: list[TarifaCandidata]
    conflictos: list[ConflictoTarifa]
    sin_cambios: int
    sin_mapear: dict[str, int]  # descripción Siges → filas wide afectadas


def _resolver_spst(
    descripcion: str, mapeo: Mapping[str, uuid.UUID | None]
) -> tuple[str, uuid.UUID | None]:
    """Devuelve (estado, spst_id): 'ok' con el SPST (None = genérica, sea por
    descripción 'Genérica' o por mapeo explícito a genérica — el caso TMT*),
    'excluida' para las descripciones basura, 'sin_mapear' si falta el mapeo."""
    normalizada = normalizar_nombre(descripcion)
    if normalizada in _DESCRIPCIONES_EXCLUIDAS:
        return ("excluida", None)
    if normalizada == _GENERICA:
        return ("ok", None)
    if descripcion in mapeo:
        return ("ok", mapeo[descripcion])
    return ("sin_mapear", None)


def _candidatas(costo: SigesCostoServicio, spst_id: uuid.UUID | None) -> list[TarifaCandidata]:
    """Una fila long por tipo con costo > 0 — un costo en 0 es "no presta ese
    servicio", no una tarifa (el caso real de $0,01 de Centro Cívico sí pasa)."""
    return [
        TarifaCandidata(tipo, spst_id, valor, costo.costo_km, costo.vigencia_desde)
        for tipo, atributo in _TIPOS
        if (valor := float(getattr(costo, atributo))) > 0
    ]


def _comparar(existente: Tarifario, candidata: TarifaCandidata) -> list[ConflictoTarifa]:
    conflictos = []
    for campo, local, siges in (
        ("costo_servicio", existente.costo_servicio, candidata.costo_servicio),
        ("costo_km", existente.costo_km, candidata.costo_km),
    ):
        if abs(local - siges) > TOLERANCIA_COSTO:
            conflictos.append(
                ConflictoTarifa(
                    tipo_servicio=candidata.tipo_servicio,
                    spst_id=candidata.spst_id,
                    vigencia_desde=candidata.vigencia_desde,
                    campo=campo,
                    valor_local=local,
                    valor_siges=siges,
                )
            )
    return conflictos


def planificar_sync_tarifarios(
    existentes: list[Tarifario],
    costos: list[SigesCostoServicio],
    mapeo_spst: Mapping[str, uuid.UUID | None],
) -> PlanSyncTarifarios:
    por_clave = {(t.tipo_servicio, t.spst_id, t.vigencia_desde): t for t in existentes}
    a_crear: list[TarifaCandidata] = []
    conflictos: list[ConflictoTarifa] = []
    sin_cambios = 0
    sin_mapear: Counter[str] = Counter()

    for costo in costos:
        estado, spst_id = _resolver_spst(costo.descripcion, mapeo_spst)
        if estado == "excluida":
            continue
        if estado == "sin_mapear":
            sin_mapear[costo.descripcion] += 1
            continue
        for candidata in _candidatas(costo, spst_id):
            clave = (candidata.tipo_servicio, candidata.spst_id, candidata.vigencia_desde)
            existente = por_clave.get(clave)
            if existente is None:
                a_crear.append(candidata)
                continue
            diferencias = _comparar(existente, candidata)
            conflictos.extend(diferencias)
            sin_cambios += 0 if diferencias else 1

    return PlanSyncTarifarios(
        a_crear=a_crear,
        conflictos=conflictos,
        sin_cambios=sin_cambios,
        sin_mapear=dict(sin_mapear),
    )


def _matchea(normalizada: str, spst: Spst) -> bool:
    if nombres_compatibles(normalizada, normalizar_nombre(spst.nombre)):
        return True
    return bool(spst.zona_cobertura) and nombres_compatibles(
        normalizada, normalizar_nombre(spst.zona_cobertura or "")
    )


def proponer_mapeo_spst(descripciones: list[str], spsts: list[Spst]) -> dict[str, uuid.UUID]:
    """Propuesta automática descripción-Siges → SPST: matchea el nombre del SPST
    o su `zona_cobertura` (solo esa, texto libre de ayuda — ver esa entidad).
    Solo matches únicos en ambas direcciones (mismo criterio que
    `proponer_vinculos`). La confirmación es siempre manual."""
    por_descripcion: dict[str, uuid.UUID] = {}
    for descripcion in descripciones:
        normalizada = normalizar_nombre(descripcion)
        matches = [s for s in spsts if _matchea(normalizada, s)]
        if len(matches) == 1:
            por_descripcion[descripcion] = matches[0].id
    usos = Counter(por_descripcion.values())
    return {d: spst_id for d, spst_id in por_descripcion.items() if usos[spst_id] == 1}
