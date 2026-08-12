"""ALT005 — Ruta Compartida (`evaluar_grupo`): agrupa incidentes del mismo día en el
mismo corredor y genera una `ObservacionGenerada` por grupo. Es la interfaz "actual"
del legacy (la única con test de caracterización — ver
`LIQUIDACION_PRESTADORES_CARACTERIZACION.md` §7); el path por-incidente legado
(`evaluar()`, back-compat) vive en `alt005_ruta_individual.py`. Desactivada por
default (`ReglaAlerta.activa=False` en `seed.py`) — decisión de alcance confirmada
por el usuario, se porta tal cual, no se activa."""

import uuid
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.services.motor_reglas._resolucion import mismo_corredor
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import (
    ObservacionGenerada,
)


def evaluar_grupo_alt005(
    incidentes: Sequence[Incidente], tablas_por_incidente: Mapping[uuid.UUID, TablaKm]
) -> list[ObservacionGenerada]:
    con_tabla = [i for i in incidentes if i.id in tablas_por_incidente]
    por_dia = _agrupar_por_dia(con_tabla)
    observaciones: list[ObservacionGenerada] = []
    procesados: set[uuid.UUID] = set()
    for incs_dia in por_dia.values():
        observaciones += _observaciones_del_dia(incs_dia, tablas_por_incidente, procesados)
    return observaciones


def _agrupar_por_dia(incidentes: Sequence[Incidente]) -> dict[date, list[Incidente]]:
    por_dia: dict[date, list[Incidente]] = defaultdict(list)
    for inc in incidentes:
        if inc.fecha_cierre and (inc.cant_km_cobrado or 0) > 0:
            por_dia[inc.fecha_cierre].append(inc)
    return por_dia


def _observaciones_del_dia(
    incs_dia: Sequence[Incidente],
    tablas: Mapping[uuid.UUID, TablaKm],
    procesados: set[uuid.UUID],
) -> list[ObservacionGenerada]:
    observaciones = []
    for inc in incs_dia:
        obs = _observacion_para(inc, incs_dia, tablas, procesados)
        if obs:
            observaciones.append(obs)
    return observaciones


def _observacion_para(
    inc: Incidente,
    incs_dia: Sequence[Incidente],
    tablas: Mapping[uuid.UUID, TablaKm],
    procesados: set[uuid.UUID],
) -> ObservacionGenerada | None:
    if inc.id in procesados:
        return None
    tabla_actual = tablas[inc.id]
    if not tabla_actual.spst_id and not tabla_actual.localidad_cliente:
        return None
    grupo = _armar_grupo(inc, tabla_actual, incs_dia, tablas, procesados)
    if len(grupo) < 2:
        return None
    procesados.update(g.id for g in grupo)
    return _crear_observacion(grupo, tablas)


def _armar_grupo(
    inc: Incidente,
    tabla_actual: TablaKm,
    incs_dia: Sequence[Incidente],
    tablas: Mapping[uuid.UUID, TablaKm],
    procesados: set[uuid.UUID],
) -> list[Incidente]:
    grupo = [inc]
    for otro in incs_dia:
        if otro.id == inc.id or otro.id in procesados:
            continue
        tabla_otro = tablas.get(otro.id)
        if tabla_otro and mismo_corredor(tabla_actual, tabla_otro):
            grupo.append(otro)
    return grupo


def _crear_observacion(
    grupo: list[Incidente], tablas: Mapping[uuid.UUID, TablaKm]
) -> ObservacionGenerada:
    km_totales = sum(g.cant_km_cobrado or 0 for g in grupo)
    km_max_tabla = max((tablas[g.id].kms_recorrido or 0) for g in grupo)
    diferencia_km = km_totales - km_max_tabla
    monto_cobrado_total = sum(g.costo_total_cobrado or 0 for g in grupo)
    principal = max(grupo, key=lambda g: g.cant_km_cobrado or 0)
    severidad, titulo, _diferencia_monto, monto_esperado = _clasificar(
        grupo, km_totales, diferencia_km, monto_cobrado_total, principal
    )
    return ObservacionGenerada(
        tipo_observacion="RUTA_COMPARTIDA",
        severidad=severidad,
        titulo=titulo,
        descripcion=_descripcion(grupo, tablas, km_totales, km_max_tabla),
        monto_cobrado=monto_cobrado_total,
        monto_esperado=monto_esperado,
        incidentes_relacionados=[g.id for g in grupo],
        incidente_principal_id=principal.id,
        regla_codigo="ALT005",
        datos_contexto=_contexto(grupo, tablas, principal, km_max_tabla, diferencia_km),
    )


def _clasificar(
    grupo: list[Incidente],
    km_totales: float,
    diferencia_km: float,
    monto_cobrado_total: float,
    principal: Incidente,
) -> tuple[str, str, float, float]:
    if km_totales == 0:
        titulo = f"Ruta compartida correctamente agrupada — {len(grupo)} incidentes"
        return "INFORMATIVO", titulo, 0.0, monto_cobrado_total
    if diferencia_km > 0:
        return _clasificar_exceso(diferencia_km, monto_cobrado_total, principal)
    titulo = f"Posible ruta compartida — revisar {len(grupo)} incidentes"
    return "ADVERTENCIA", titulo, 0.0, monto_cobrado_total


def _clasificar_exceso(
    diferencia_km: float, monto_cobrado_total: float, principal: Incidente
) -> tuple[str, str, float, float]:
    costo_km_unit = _costo_km_unitario(principal)
    diferencia_monto = round(diferencia_km * costo_km_unit, 2)
    monto_esperado = round(monto_cobrado_total - diferencia_monto, 2)
    titulo = f"KMs duplicados en corredor — ${diferencia_monto:,.2f} cobrado en exceso"
    return "CRITICO", titulo, diferencia_monto, monto_esperado


def _costo_km_unitario(principal: Incidente) -> float:
    if (principal.cant_km_cobrado or 0) > 0:
        return (principal.total_viaje_cobrado or 0) / principal.cant_km_cobrado
    return principal.costo_km_cobrado or 0


def _descripcion(
    grupo: list[Incidente],
    tablas: Mapping[uuid.UUID, TablaKm],
    km_totales: float,
    km_max_tabla: float,
) -> str:
    empresa = grupo[0].empresa_nombre or "?"
    fecha_str = str(grupo[0].fecha_cierre)
    localidades = _localidades(grupo, tablas)
    return (
        f"{len(grupo)} incidentes de {empresa} el {fecha_str} "
        f"en corredor ({', '.join(localidades)}). "
        f"KMs cobrados total: {km_totales} | KMs máx. corredor (tabla): {km_max_tabla}."
    )


def _localidades(grupo: list[Incidente], tablas: Mapping[uuid.UUID, TablaKm]) -> list[str]:
    return [(tablas[g.id].localidad_cliente or g.sucursal_nombre or "?") for g in grupo]


def _contexto(
    grupo: list[Incidente],
    tablas: Mapping[uuid.UUID, TablaKm],
    principal: Incidente,
    km_max_tabla: float,
    diferencia_km: float,
) -> dict[str, Any]:
    roles = {g.id: "referencia" for g in grupo}
    roles[principal.id] = "principal"
    return {
        "localidades": _localidades(grupo, tablas),
        "km_individuales": {g.numero_incidente: g.cant_km_cobrado or 0 for g in grupo},
        "km_maximo_corredor_tabla": km_max_tabla,
        "diferencia_km": round(diferencia_km, 2),
        "roles": {g.numero_incidente: roles[g.id] for g in grupo},
    }
