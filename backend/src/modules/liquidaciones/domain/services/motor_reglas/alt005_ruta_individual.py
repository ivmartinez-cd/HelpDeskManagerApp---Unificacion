"""ALT005 — Ruta Compartida, camino por-incidente (`evaluar()` del legacy): genera
Alertas individuales cuando un incidente comparte localidad o corredor con otro del
mismo día en la misma liquidación. Complementa — no sustituye — el camino de grupo de
`alt005_ruta.py` (que genera Observaciones agrupadas por corredor): el legacy corría
ambos siempre juntos para la misma regla activa, sin excluirse entre sí, y así se
porta acá (ver `LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md` para el detalle de por
qué este camino no se había portado antes).

Divergencia consciente vs. el legacy: el legacy resolvía la TablaKm del incidente
actual con `ILIKE` (case-insensitive) pero la de los "hermanos" con `==` exacto
(case-sensitive) — asimetría que parece un bug accidental, no una decisión de diseño.
Acá se usa la misma normalización uniforme (`resolver_tabla_km`/
`clave_empresa_sucursal`, ambos lados `.strip().lower()`) que ya usan todos los
evaluadores del motor nuevo.

Dos ramas del legacy (`"agrupado_ok"`, `"corredor_agrupado_ok"`) son código muerto: la
guarda de km cobrado > 0 las vuelve inalcanzables (confirmado contra los datos reales
de producción — 0 apariciones en 81 alertas) — no se portan.
"""

from collections.abc import Sequence
from typing import Any

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.services.motor_reglas._resolucion import (
    misma_localidad,
    mismo_spst_dentro_del_umbral,
)
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import Hallazgo

_Vecino = tuple[Incidente, TablaKm | None]
_Candidato = tuple[Incidente, TablaKm]


def evaluar_alt005(
    incidente: Incidente, tabla_km: TablaKm | None, vecinos_mismo_dia: Sequence[_Vecino]
) -> list[Hallazgo]:
    if not incidente.fecha_cierre:
        return []
    cobrado = incidente.cant_km_cobrado or 0
    if cobrado == 0:
        return []
    if tabla_km is None:
        return []

    candidatos: list[_Candidato] = [(i, t) for i, t in vecinos_mismo_dia if t is not None]
    exactos = [(i, t) for i, t in candidatos if misma_localidad(tabla_km, t)]
    exactos_ids = {i.id for i, _ in exactos}
    corredor = [
        (i, t)
        for i, t in candidatos
        if i.id not in exactos_ids and mismo_spst_dentro_del_umbral(tabla_km, t)
    ]

    hallazgos: list[Hallazgo] = []
    if exactos:
        hallazgos += _hallazgo_exactos(cobrado, exactos, tabla_km)
    if corredor:
        hallazgos += _hallazgo_corredor(cobrado, corredor, tabla_km)
    return hallazgos


def _hallazgo_exactos(
    cobrado: float, exactos: Sequence[_Candidato], tabla_km: TablaKm
) -> list[Hallazgo]:
    duplicados = [i for i, _ in exactos if (i.cant_km_cobrado or 0) > 0]
    if not duplicados:
        return []
    refs = ", ".join(f"#{i.numero_incidente} ({i.cant_km_cobrado} km)" for i in duplicados)
    descripcion = (
        f"Ruta compartida con KMs cobrados duplicados: se cobraron {cobrado} km "
        f"en este incidente y también en: {refs} en la misma fecha y localidad."
    )
    contexto: dict[str, Any] = {
        "tipo": "duplicado",
        "cobrado_este": cobrado,
        "otros_incidentes": [i.numero_incidente for i in duplicados],
        "localidad": tabla_km.localidad_cliente,
    }
    return [Hallazgo(descripcion, contexto)]


def _hallazgo_corredor(
    cobrado: float, corredor: Sequence[_Candidato], tabla_km: TablaKm
) -> list[Hallazgo]:
    duplicados = [(i, t) for i, t in corredor if (i.cant_km_cobrado or 0) > 0]
    if duplicados:
        return [_hallazgo_corredor_duplicado(cobrado, duplicados, tabla_km)]
    sin_km = [(i, t) for i, t in corredor if (i.cant_km_cobrado or 0) == 0]
    if not sin_km:
        return []
    return [_hallazgo_corredor_contenido(cobrado, sin_km, tabla_km)]


def _hallazgo_corredor_duplicado(
    cobrado: float, duplicados: Sequence[_Candidato], tabla_km: TablaKm
) -> Hallazgo:
    refs = ", ".join(
        f"#{i.numero_incidente} ({i.cant_km_cobrado} km, {t.localidad_cliente})"
        for i, t in duplicados
    )
    descripcion = (
        f"Corredor de ruta compartido: se cobraron {cobrado} km en este incidente "
        f"y también km en: {refs} el mismo día (mismo SPST, diferencia ≤ 50 km)."
    )
    contexto: dict[str, Any] = {
        "tipo": "corredor_duplicado",
        "cobrado_este": cobrado,
        "km_actual": tabla_km.kms_recorrido,
        "otros_incidentes": [i.numero_incidente for i, _ in duplicados],
        "spst_id": str(tabla_km.spst_id),
    }
    return Hallazgo(descripcion, contexto)


def _hallazgo_corredor_contenido(
    cobrado: float, sin_km: Sequence[_Candidato], tabla_km: TablaKm
) -> Hallazgo:
    refs = ", ".join(
        f"#{i.numero_incidente} ({t.localidad_cliente}, {t.kms_recorrido} km esperados)"
        for i, t in sin_km
    )
    descripcion = (
        f"Este incidente cobró {cobrado} km incluyendo el tramo compartido con: {refs} "
        f"del mismo corredor. Verificar si es un único viaje o viajes separados."
    )
    contexto: dict[str, Any] = {
        "tipo": "corredor_contenido",
        "cobrado_este": cobrado,
        "km_actual": tabla_km.kms_recorrido,
        "otros_incidentes": [i.numero_incidente for i, _ in sin_km],
        "spst_id": str(tabla_km.spst_id),
    }
    return Hallazgo(descripcion, contexto)
