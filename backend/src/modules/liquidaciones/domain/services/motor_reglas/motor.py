"""Orquestador del motor de reglas — versión de dominio, pura (sin DB): recibe todos
los datos ya cargados por la aplicación y devuelve el resultado completo. Reemplaza a
`motor_reglas.py::ejecutar_motor` del legacy, que consultaba la DB desde adentro de
cada evaluador (prohibido en esta capa, ver ARCHITECTURE_GUIDE.md §3 — Domain no
importa DB/frameworks).

ALT005 corre por LOS DOS caminos, igual que en el legacy: `evaluar_alt005` (módulo
`alt005_ruta_individual`) por-incidente, vía `_EVALUADORES_POR_INCIDENTE`, genera
`AlertaGenerada` (`es_grupo=False`) gateada por `regla.activa` (igual que cualquier
otra regla); `evaluar_grupo_alt005` (módulo `alt005_ruta`) agrupa por corredor y
genera `AlertaGenerada` (`es_grupo=True`) vía `_evaluar_alertas_grupo`, con su propio
switch anidado (`regla_alerta.genera_observaciones`, en `configuracion` — nombre
heredado de cuando esto era una entidad `Observacion` separada, ver
`domain/entities/alerta.py` — desde la auditoría de liquidaciones, hallazgo "un
switch controla dos comportamientos en ALT005"): sigue requiriendo `activa=True`,
pero puede desactivarse por separado sin apagar la Alerta por-incidente.
"""

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.modules.liquidaciones.domain.entities.incidente import (
    ESTADO_VALIDACION_CON_ALERTAS,
    ESTADO_VALIDACION_OK,
    Incidente,
)
from src.modules.liquidaciones.domain.entities.regla_alerta import (
    CODIGO_ALT001_PRECIO_INCORRECTO,
    CODIGO_ALT002_KMS_INCORRECTOS,
    CODIGO_ALT003_VIATICO_DUPLICADO,
    CODIGO_ALT004_SERVICIO_DUPLICADO,
    CODIGO_ALT005_RUTA_COMPARTIDA,
    CODIGO_ALT008_TARIFARIO_INEXISTENTE,
    CODIGO_ALT009_PAR_EMPRESA_SUCURSAL,
    CODIGO_ALT010_SERIE_DUPLICADA,
    ReglaAlerta,
    genera_observaciones,
)
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.entities.tarifario import (
    TIPO_CORRECTIVO,
    TIPO_PREVENTIVO,
    Tarifario,
)
from src.modules.liquidaciones.domain.services.motor_reglas import (
    alt001_precio,
    alt002_km,
    alt003_viatico,
    alt004_duplicado,
    alt005_ruta_individual,
    alt008_tarifario,
    alt009_spst,
    alt010_serie_duplicada,
)
from src.modules.liquidaciones.domain.services.motor_reglas._resolucion import (
    indexar_tablas_km,
    resolver_tabla_km,
    resolver_tarifario,
)
from src.modules.liquidaciones.domain.services.motor_reglas.alt005_ruta import (
    evaluar_grupo_alt005,
)
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import (
    AlertaGenerada,
    Hallazgo,
    IncidenteEvaluado,
    ResultadoMotorReglas,
)

_EVALUADORES_POR_INCIDENTE = (
    CODIGO_ALT001_PRECIO_INCORRECTO,
    CODIGO_ALT002_KMS_INCORRECTOS,
    CODIGO_ALT003_VIATICO_DUPLICADO,
    CODIGO_ALT004_SERVICIO_DUPLICADO,
    CODIGO_ALT005_RUTA_COMPARTIDA,
    CODIGO_ALT008_TARIFARIO_INEXISTENTE,
    CODIGO_ALT009_PAR_EMPRESA_SUCURSAL,
    CODIGO_ALT010_SERIE_DUPLICADA,
)


@dataclass(frozen=True)
class _ContextoMotor:
    reglas_activas: Mapping[str, ReglaAlerta]
    indice_tablas: Mapping[tuple[str, str], TablaKm]
    tarifarios: Sequence[Tarifario]
    incidentes_liquidacion: Sequence[Incidente]
    incidentes_prestador: Sequence[Incidente]


def ejecutar_motor_reglas(
    incidentes: Sequence[Incidente],
    incidentes_prestador: Sequence[Incidente],
    reglas_activas: Mapping[str, ReglaAlerta],
    tablas_km: Sequence[TablaKm],
    tarifarios: Sequence[Tarifario],
) -> ResultadoMotorReglas:
    """Ya no recibe `spsts`: el tarifario se resuelve directo por
    `TablaKm.spst_id` (ver `_resolucion.py`) — el SPST en sí no le hace falta
    a ninguna regla desde que la zona dejó de ser el intermediario."""
    contexto = _ContextoMotor(
        reglas_activas=reglas_activas,
        indice_tablas=indexar_tablas_km(tablas_km),
        tarifarios=tarifarios,
        incidentes_liquidacion=incidentes,
        incidentes_prestador=incidentes_prestador,
    )
    incidentes_evaluados, alertas = _evaluar_incidentes(incidentes, contexto)
    alertas = alertas + _evaluar_alertas_grupo(incidentes, contexto)
    return ResultadoMotorReglas(incidentes_evaluados, alertas)


def _evaluar_incidentes(
    incidentes: Sequence[Incidente], contexto: _ContextoMotor
) -> tuple[list[IncidenteEvaluado], list[AlertaGenerada]]:
    incidentes_evaluados = []
    alertas: list[AlertaGenerada] = []
    for incidente in incidentes:
        tabla_km, tarifario, hallazgos = _evaluar_incidente(incidente, contexto)
        alertas += [_a_alerta(incidente.id, c, h, contexto.reglas_activas[c]) for c, h in hallazgos]
        estado = ESTADO_VALIDACION_CON_ALERTAS if hallazgos else ESTADO_VALIDACION_OK
        incidentes_evaluados.append(_a_incidente_evaluado(incidente, tabla_km, tarifario, estado))
    return incidentes_evaluados, alertas


def _evaluar_incidente(
    incidente: Incidente, contexto: _ContextoMotor
) -> tuple[TablaKm | None, Tarifario | None, list[tuple[str, Hallazgo]]]:
    tabla_km = resolver_tabla_km(incidente, contexto.indice_tablas)
    spst_id = tabla_km.spst_id if tabla_km else None
    tarifario = resolver_tarifario(incidente, spst_id, contexto.tarifarios)
    hallazgos = []
    for codigo in _EVALUADORES_POR_INCIDENTE:
        regla = contexto.reglas_activas.get(codigo)
        if regla is None:
            continue
        args = (incidente, tabla_km, tarifario, spst_id, contexto, regla)
        hallazgos += [(codigo, h) for h in _evaluar_regla(codigo, *args)]
    return tabla_km, tarifario, hallazgos


def _evaluar_regla(
    codigo: str,
    incidente: Incidente,
    tabla_km: TablaKm | None,
    tarifario: Tarifario | None,
    spst_id: uuid.UUID | None,
    contexto: _ContextoMotor,
    regla: ReglaAlerta,
) -> list[Hallazgo]:
    if codigo == CODIGO_ALT001_PRECIO_INCORRECTO:
        return alt001_precio.evaluar_alt001(incidente, tarifario)
    if codigo == CODIGO_ALT002_KMS_INCORRECTOS:
        return _evaluar_alt002(incidente, tabla_km, contexto, regla)
    if codigo == CODIGO_ALT003_VIATICO_DUPLICADO:
        similares = _similares_alt003(incidente, contexto.incidentes_prestador)
        return alt003_viatico.evaluar_alt003(incidente, similares)
    if codigo == CODIGO_ALT004_SERVICIO_DUPLICADO:
        duplicados = _duplicados_alt004(incidente, contexto.incidentes_prestador)
        return alt004_duplicado.evaluar_alt004(incidente, duplicados)
    if codigo == CODIGO_ALT005_RUTA_COMPARTIDA:
        return _evaluar_alt005(incidente, tabla_km, contexto)
    if codigo == CODIGO_ALT008_TARIFARIO_INEXISTENTE:
        return alt008_tarifario.evaluar_alt008(incidente, tarifario, spst_id)
    if codigo == CODIGO_ALT009_PAR_EMPRESA_SUCURSAL:
        return alt009_spst.evaluar_alt009(incidente, tabla_km)
    coincidencias = _coincidencias_alt010(incidente, contexto.incidentes_prestador)
    return alt010_serie_duplicada.evaluar_alt010(incidente, coincidencias)


def _evaluar_alt005(
    incidente: Incidente, tabla_km: TablaKm | None, contexto: _ContextoMotor
) -> list[Hallazgo]:
    vecinos = _vecinos_mismo_dia(incidente, contexto)
    return alt005_ruta_individual.evaluar_alt005(incidente, tabla_km, vecinos)


def _evaluar_alt002(
    incidente: Incidente, tabla_km: TablaKm | None, contexto: _ContextoMotor, regla: ReglaAlerta
) -> list[Hallazgo]:
    tolerancia = (regla.configuracion or {}).get("tolerancia_km", 0.5)
    vecinos = _vecinos_mismo_dia(incidente, contexto)
    return alt002_km.evaluar_alt002(incidente, tabla_km, vecinos, tolerancia)


def _vecinos_mismo_dia(
    incidente: Incidente, contexto: _ContextoMotor
) -> list[tuple[Incidente, TablaKm | None]]:
    vecinos = []
    for otro in contexto.incidentes_liquidacion:
        if otro.id == incidente.id or otro.fecha_cierre != incidente.fecha_cierre:
            continue
        vecinos.append((otro, resolver_tabla_km(otro, contexto.indice_tablas)))
    return vecinos


def _similares_alt003(
    incidente: Incidente, incidentes_prestador: Sequence[Incidente]
) -> list[Incidente]:
    return [
        i
        for i in incidentes_prestador
        if i.id != incidente.id
        and _mismo_texto(i.empresa_nombre, incidente.empresa_nombre)
        and _mismo_texto(i.sucursal_nombre, incidente.sucursal_nombre)
        and i.fecha_cierre == incidente.fecha_cierre
        and (i.cant_km_cobrado or 0) > 0
    ]


def _mismo_texto(a: str | None, b: str | None) -> bool:
    return (a or "").strip().lower() == (b or "").strip().lower()


def _duplicados_alt004(
    incidente: Incidente, incidentes_prestador: Sequence[Incidente]
) -> list[Incidente]:
    return [
        i
        for i in incidentes_prestador
        if i.id != incidente.id and i.numero_incidente == incidente.numero_incidente
    ]


def _coincidencias_alt010(
    incidente: Incidente, incidentes_prestador: Sequence[Incidente]
) -> list[Incidente]:
    if not incidente.nro_serie or incidente.fecha_cierre is None:
        return []
    if incidente.tipo not in (TIPO_PREVENTIVO, TIPO_CORRECTIVO):
        return []
    tipo_opuesto = TIPO_CORRECTIVO if incidente.tipo == TIPO_PREVENTIVO else TIPO_PREVENTIVO
    periodo = (incidente.fecha_cierre.year, incidente.fecha_cierre.month)
    return [
        i
        for i in incidentes_prestador
        if i.id != incidente.id
        and i.nro_serie == incidente.nro_serie
        and i.tipo == tipo_opuesto
        and i.fecha_cierre is not None
        and (i.fecha_cierre.year, i.fecha_cierre.month) == periodo
    ]


def _a_alerta(
    incidente_id: uuid.UUID, codigo: str, hallazgo: Hallazgo, regla: ReglaAlerta
) -> AlertaGenerada:
    return AlertaGenerada(
        incidente_id=incidente_id,
        tipo_alerta=codigo,
        descripcion=hallazgo.descripcion,
        riesgo=regla.riesgo_base,
        datos_contexto=hallazgo.contexto,
    )


def _a_incidente_evaluado(
    incidente: Incidente, tabla_km: TablaKm | None, tarifario: Tarifario | None, estado: str
) -> IncidenteEvaluado:
    return IncidenteEvaluado(
        incidente_id=incidente.id,
        costo_servicio_esperado=tarifario.costo_servicio if tarifario else None,
        costo_km_esperado=tarifario.costo_km if tarifario else None,
        cant_km_esperado=tabla_km.kms_a_facturar if tabla_km else None,
        estado_validacion=estado,
    )


def _evaluar_alertas_grupo(
    incidentes: Sequence[Incidente], contexto: _ContextoMotor
) -> list[AlertaGenerada]:
    regla = contexto.reglas_activas.get(CODIGO_ALT005_RUTA_COMPARTIDA)
    if regla is None or not genera_observaciones(regla):
        return []
    tablas_por_incidente = {}
    for inc in incidentes:
        tabla = resolver_tabla_km(inc, contexto.indice_tablas)
        if tabla is not None:
            tablas_por_incidente[inc.id] = tabla
    return evaluar_grupo_alt005(incidentes, tablas_por_incidente)
