"""Planificación pura del sync de tarifarios desde Siges (ADR-014, dataset 2).

Pivot wide→long de `CostoServicio` + resolución de zona + plan de acciones:
- crear: la vigencia (tipo, zona, vigencia_desde) no existe localmente.
- conflicto: existe pero con costo distinto — se reporta, NUNCA se escribe.
- sin_cambios: existe con los mismos costos (tolerancia 0.01, la de ALT001).
Descripciones sin mapeo de zona quedan fuera del plan y se reportan aparte.
"""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

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
_ZONA_GENERICA = "generica"
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
    zona: str | None
    costo_servicio: float
    costo_km: float
    vigencia_desde: date


@dataclass(frozen=True)
class ConflictoTarifa:
    tipo_servicio: str
    zona: str | None
    vigencia_desde: date
    campo: str
    valor_local: float
    valor_siges: float


@dataclass(frozen=True)
class PlanSyncTarifarios:
    a_crear: list[TarifaCandidata]
    conflictos: list[ConflictoTarifa]
    sin_cambios: int
    zonas_sin_mapear: dict[str, int]  # descripción Siges → filas wide afectadas


def _resolver_zona(descripcion: str, mapeo: Mapping[str, str | None]) -> tuple[str, str | None]:
    """Devuelve (estado, zona): 'ok' con la zona local (None = genérica, sea por
    descripción 'Genérica' o por mapeo explícito a genérica — el caso TMT*),
    'excluida' para las descripciones basura, 'sin_mapear' si falta el mapeo."""
    normalizada = normalizar_nombre(descripcion)
    if normalizada in _DESCRIPCIONES_EXCLUIDAS:
        return ("excluida", None)
    if normalizada == _ZONA_GENERICA:
        return ("ok", None)
    if descripcion in mapeo:
        return ("ok", mapeo[descripcion])
    return ("sin_mapear", None)


def _candidatas(costo: SigesCostoServicio, zona: str | None) -> list[TarifaCandidata]:
    """Una fila long por tipo con costo > 0 — un costo en 0 es "no presta ese
    servicio", no una tarifa (el caso real de $0,01 de Centro Cívico sí pasa)."""
    return [
        TarifaCandidata(tipo, zona, valor, costo.costo_km, costo.vigencia_desde)
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
                    zona=candidata.zona,
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
    mapeo_zonas: Mapping[str, str | None],
) -> PlanSyncTarifarios:
    por_clave = {(t.tipo_servicio, t.zona, t.vigencia_desde): t for t in existentes}
    a_crear: list[TarifaCandidata] = []
    conflictos: list[ConflictoTarifa] = []
    sin_cambios = 0
    zonas_sin_mapear: Counter[str] = Counter()

    for costo in costos:
        estado, zona = _resolver_zona(costo.descripcion, mapeo_zonas)
        if estado == "excluida":
            continue
        if estado == "sin_mapear":
            zonas_sin_mapear[costo.descripcion] += 1
            continue
        for candidata in _candidatas(costo, zona):
            clave = (candidata.tipo_servicio, candidata.zona, candidata.vigencia_desde)
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
        zonas_sin_mapear=dict(zonas_sin_mapear),
    )


def proponer_mapeo_zonas(descripciones: list[str], zonas_locales: list[str]) -> dict[str, str]:
    """Propuesta automática descripción-Siges → zona-local: solo matches únicos
    en ambas direcciones (mismo criterio que `proponer_vinculos`). La confirmación
    es siempre manual."""
    por_descripcion: dict[str, str] = {}
    for descripcion in descripciones:
        matches = [
            zona
            for zona in zonas_locales
            if nombres_compatibles(normalizar_nombre(descripcion), normalizar_nombre(zona))
        ]
        if len(matches) == 1:
            por_descripcion[descripcion] = matches[0]
    usos = Counter(por_descripcion.values())
    return {d: z for d, z in por_descripcion.items() if usos[z] == 1}
