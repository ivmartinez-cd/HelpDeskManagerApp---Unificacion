"""Genera el archivo de exportación a SiGes (REGLAS_DE_NEGOCIO §12) para un
proceso real — reusa la misma grilla cacheada que el tablero
(`GetTableroProyeccionSigesUseCase`, `PyodbcGrillaEstimacionGateway`)."""

import logging
from dataclasses import dataclass

from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.dtos.decision_operador_dto import DecisionOperadorDto
from src.modules.contadores.application.dtos.equipo_proceso_dto import (
    ClaseProceso,
    EquipoProceso,
)
from src.modules.contadores.application.dtos.fila_grilla_siges_dto import FilaGrillaSigesDto
from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.application.dtos.solicitud_tablero_siges_dto import (
    SolicitudTableroSigesDto,
)
from src.modules.contadores.application.use_cases._construir_estimacion_input import (
    construir_estimacion_input,
)
from src.modules.contadores.application.use_cases._mapear_filas_grilla_siges import (
    agrupar_por_equipo,
)
from src.modules.contadores.application.use_cases._resolver_resultado_final import (
    resolver_resultado_final,
)
from src.modules.contadores.domain.ports.decisiones_operador_port import DecisionesOperadorPort
from src.modules.contadores.domain.ports.estim_log_port import EstimLogPort, ResumenAuditoriaMaquina
from src.modules.contadores.domain.ports.grilla_estimacion_port import GrillaEstimacionPort
from src.modules.contadores.domain.ports.recesos_port import RecesosPort
from src.modules.contadores.domain.services.estimacion.export_csv import (
    ENCABEZADO_CSV,
    escape_csv,
    motivo_de_fuente,
    sanitizar_simbolos,
    tipo_toma_export,
)
from src.modules.contadores.domain.services.estimacion.motor import estimar
from src.modules.contadores.domain.services.estimacion.resumen_observacion import (
    DatosObservacion,
    armar_resumen_observacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.receso_cliente import RecesoCliente

logger = logging.getLogger(__name__)

_CLASE_MONO = "10"
_CLASE_COLOR = "20"


class GenerarExportCsvUseCase:
    def __init__(
        self,
        gateway: GrillaEstimacionPort,
        decisiones: DecisionesOperadorPort,
        recesos_store: RecesosPort,
        estim_log: EstimLogPort,
    ) -> None:
        self._gateway = gateway
        self._decisiones = decisiones
        self._recesos_store = recesos_store
        self._estim_log = estim_log

    async def execute(self, solicitud: SolicitudTableroSigesDto) -> str:
        filas_siges = await self._gateway.fetch_grilla(
            solicitud.nro_proceso, solicitud.fecha_objetivo
        )
        if not filas_siges:
            return ENCABEZADO_CSV + "\r\n"
        equipos = agrupar_por_equipo(filas_siges)
        ctx = await self._contexto(filas_siges[0], solicitud)
        todas_decisiones = await self._decisiones.listar_todas()
        auditoria = await self._estim_log.resumen_por_maquina(solicitud.nro_proceso)
        equipos_ordenados = sorted(equipos, key=lambda e: (e.empresa, e.sucursal, e.nro_serie))
        filas_csv = [
            _fila_csv_de(equipo, ctx, todas_decisiones, auditoria) for equipo in equipos_ordenados
        ]
        return ENCABEZADO_CSV + "\r\n" + "".join(f + "\r\n" for f in filas_csv if f is not None)

    async def _contexto(
        self, fila: FilaGrillaSigesDto, solicitud: SolicitudTableroSigesDto
    ) -> ContextoProcesoDto:
        recesos = await self._recesos_store.listar(solicitud.id_grupo_economico)
        return ContextoProcesoDto(
            fecha_objetivo=solicitud.fecha_objetivo,
            periodo_desde=fila.periodo_desde,
            periodo_hasta=fila.periodo_hasta,
            id_grupo_economico=solicitud.id_grupo_economico,
            id_anexo=solicitud.id_anexo,
            recesos=[_a_receso_cliente(r) for r in recesos],
        )


@dataclass(frozen=True, slots=True)
class _ClaseResuelta:
    clase: ClaseProceso
    entrada: EstimacionInput
    resultado: EstimacionResultado
    es_manual: bool


def _fila_csv_de(
    equipo: EquipoProceso,
    ctx: ContextoProcesoDto,
    todas_decisiones: dict[tuple[int, str], DecisionOperadorDto],
    auditoria: dict[int, ResumenAuditoriaMaquina],
) -> str | None:
    cl10 = _resolver_clase(equipo, _CLASE_MONO, ctx, todas_decisiones)
    cl20 = _resolver_clase(equipo, _CLASE_COLOR, ctx, todas_decisiones)
    if cl10 is None and cl20 is None:
        _log_equipo_omitido(equipo)
        return None
    principal = cl10 or cl20
    assert principal is not None
    secundario = cl20 if cl10 is not None else None
    resumen = auditoria.get(equipo.id_maquina)
    observacion = _observacion_de(principal, secundario, resumen)
    return _columnas_csv(equipo, ctx, principal, secundario, observacion)


def _log_equipo_omitido(equipo: EquipoProceso) -> None:
    # Bug conocido del legacy (CsvExportService.cs, NEXT_SESSION.md
    # 2026-06-12): un equipo sin Cl.10 ni Cl.20 (solo Cl.30, digitalización)
    # tira NRE ahí. Acá se saltea con un log en vez de romper todo el export
    # — nunca se vio en la práctica según esa misma nota.
    logger.warning(
        "Equipo sin clase 10 ni 20, se omite del export",
        extra={"id_maquina": equipo.id_maquina, "nro_serie": equipo.nro_serie},
    )


def _columnas_csv(
    equipo: EquipoProceso,
    ctx: ContextoProcesoDto,
    principal: _ClaseResuelta,
    secundario: _ClaseResuelta | None,
    observacion: str,
) -> str:
    return ";".join(
        [
            escape_csv(equipo.nro_serie),
            ctx.fecha_objetivo.strftime("%d/%m/%Y"),
            tipo_toma_export(principal.resultado.tipo_toma),
            principal.clase.clase,
            _contador_str(principal.resultado.estim_propuesto),
            secundario.clase.clase if secundario else "",
            _contador_str(secundario.resultado.estim_propuesto) if secundario else "",
            motivo_de_fuente(principal.resultado.fuente),
            escape_csv(observacion),
        ]
    )


def _resolver_clase(
    equipo: EquipoProceso,
    clase_numero: str,
    ctx: ContextoProcesoDto,
    todas_decisiones: dict[tuple[int, str], DecisionOperadorDto],
) -> _ClaseResuelta | None:
    clase = next((c for c in equipo.clases if c.clase == clase_numero), None)
    if clase is None:
        return None
    entrada = construir_estimacion_input(equipo, clase, ctx)
    automatico = estimar(entrada)
    decision = todas_decisiones.get((equipo.id_maquina, clase.clase))
    resultado = resolver_resultado_final(clase, automatico, decision)
    return _ClaseResuelta(clase, entrada, resultado, bool(decision and decision.manual))


def _observacion_de(
    principal: _ClaseResuelta,
    secundario: _ClaseResuelta | None,
    resumen: ResumenAuditoriaMaquina | None,
) -> str:
    resultados = _resultados_por_tecnologia(principal, secundario)
    manual_observado = resumen.observacion_manual if resumen else None
    texto_operador = sanitizar_simbolos(manual_observado) if manual_observado else None
    datos = DatosObservacion(
        resultados=resultados,
        entrada=principal.entrada,
        texto_operador=texto_operador,
        id_auditoria=resumen.id_log_corto if resumen else None,
        forzado_por_operador=principal.es_manual or bool(secundario and secundario.es_manual),
    )
    return armar_resumen_observacion(datos)


def _resultados_por_tecnologia(
    principal: _ClaseResuelta, secundario: _ClaseResuelta | None
) -> dict[str, EstimacionResultado]:
    if secundario is None:
        return {"": principal.resultado}
    return {"Mono": principal.resultado, "Color": secundario.resultado}


def _contador_str(valor: float | None) -> str:
    return "" if valor is None else str(round(valor))


def _a_receso_cliente(r: RecesoDto) -> RecesoCliente:
    return RecesoCliente(r.fecha_desde, r.fecha_hasta, r.id_grupo_economico, r.id_anexo)
