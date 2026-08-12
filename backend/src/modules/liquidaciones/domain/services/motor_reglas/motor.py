"""Orquestador del motor de reglas — versión de dominio, pura (sin DB): recibe todos
los datos ya cargados por la aplicación y devuelve el resultado completo. Reemplaza a
`motor_reglas.py::ejecutar_motor` del legacy, que consultaba la DB desde adentro de
cada evaluador (prohibido en esta capa, ver ARCHITECTURE_GUIDE.md §3 — Domain no
importa DB/frameworks).

ALT005 solo corre acá vía `evaluar_grupo_alt005` (genera `ObservacionGenerada`) — el
path `evaluar()` por-incidente del legacy (interfaz "backward compat", sin test de
caracterización) no se portó: es código sin cobertura para una regla que además está
desactivada por default (`activa=False`). Si se activa ALT005 alguna vez, revisar si
hace falta portar ese path también.
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
    ReglaAlerta,
)
from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.services.motor_reglas import (
    alt001_precio,
    alt002_km,
    alt003_viatico,
    alt004_duplicado,
    alt008_tarifario,
    alt009_spst,
)
from src.modules.liquidaciones.domain.services.motor_reglas._resolucion import (
    indexar_tablas_km,
    resolver_tabla_km,
    resolver_tarifario,
    resolver_zona,
)
from src.modules.liquidaciones.domain.services.motor_reglas.alt005_ruta import (
    evaluar_grupo_alt005,
)
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import (
    AlertaGenerada,
    Hallazgo,
    IncidenteEvaluado,
    ObservacionGenerada,
    ResultadoMotorReglas,
)

_EVALUADORES_POR_INCIDENTE = (
    CODIGO_ALT001_PRECIO_INCORRECTO,
    CODIGO_ALT002_KMS_INCORRECTOS,
    CODIGO_ALT003_VIATICO_DUPLICADO,
    CODIGO_ALT004_SERVICIO_DUPLICADO,
    CODIGO_ALT008_TARIFARIO_INEXISTENTE,
    CODIGO_ALT009_PAR_EMPRESA_SUCURSAL,
)


@dataclass(frozen=True)
class _ContextoMotor:
    reglas_activas: Mapping[str, ReglaAlerta]
    indice_tablas: Mapping[tuple[str, str], TablaKm]
    spsts_por_id: Mapping[uuid.UUID, Spst]
    tarifarios: Sequence[Tarifario]
    incidentes_liquidacion: Sequence[Incidente]
    incidentes_prestador: Sequence[Incidente]


def ejecutar_motor_reglas(
    incidentes: Sequence[Incidente],
    incidentes_prestador: Sequence[Incidente],
    reglas_activas: Mapping[str, ReglaAlerta],
    tablas_km: Sequence[TablaKm],
    spsts: Sequence[Spst],
    tarifarios: Sequence[Tarifario],
) -> ResultadoMotorReglas:
    contexto = _ContextoMotor(
        reglas_activas=reglas_activas,
        indice_tablas=indexar_tablas_km(tablas_km),
        spsts_por_id={s.id: s for s in spsts},
        tarifarios=tarifarios,
        incidentes_liquidacion=incidentes,
        incidentes_prestador=incidentes_prestador,
    )
    incidentes_evaluados, alertas = _evaluar_incidentes(incidentes, contexto)
    observaciones = _evaluar_observaciones(incidentes, contexto)
    return ResultadoMotorReglas(incidentes_evaluados, alertas, observaciones)


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
    zona = resolver_zona(tabla_km, contexto.spsts_por_id)
    tarifario = resolver_tarifario(incidente, zona, contexto.tarifarios)
    hallazgos = []
    for codigo in _EVALUADORES_POR_INCIDENTE:
        regla = contexto.reglas_activas.get(codigo)
        if regla is None:
            continue
        args = (incidente, tabla_km, tarifario, contexto, regla)
        hallazgos += [(codigo, h) for h in _evaluar_regla(codigo, *args)]
    return tabla_km, tarifario, hallazgos


def _evaluar_regla(
    codigo: str,
    incidente: Incidente,
    tabla_km: TablaKm | None,
    tarifario: Tarifario | None,
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
    if codigo == CODIGO_ALT008_TARIFARIO_INEXISTENTE:
        return alt008_tarifario.evaluar_alt008(incidente, tarifario)
    return alt009_spst.evaluar_alt009(incidente, tabla_km)


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


def _evaluar_observaciones(
    incidentes: Sequence[Incidente], contexto: _ContextoMotor
) -> list[ObservacionGenerada]:
    if CODIGO_ALT005_RUTA_COMPARTIDA not in contexto.reglas_activas:
        return []
    tablas_por_incidente = {}
    for inc in incidentes:
        tabla = resolver_tabla_km(inc, contexto.indice_tablas)
        if tabla is not None:
            tablas_por_incidente[inc.id] = tabla
    return evaluar_grupo_alt005(incidentes, tablas_por_incidente)
