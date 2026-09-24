"""Archivo de exportación a SiGes de un proceso real — `GrillaEstimacion.ExportarCsv`
+ `CsvExportService` del Estimador de Contadores v1.7. Exporta los equipos
EFECTIVOS del tablero: el cálculo automático o la decisión que el operador
tomó en ese proceso, resuelta igual que en el tablero (misma restauración,
P/L releída de Siges por `ID_Contador`, mismo "Descartar y empezar limpio").

"Solo estimados" deja las filas que generó el estimador con valor propuesto
(`PendienteEstimar && !RequierePendiente`), fila por fila: si en una máquina
el Mono ya es real, al CSV va solo el Color, como en el legacy."""

from dataclasses import dataclass
from datetime import datetime

from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.dtos.decision_operador_dto import (
    DecisionOperadorDto,
)
from src.modules.contadores.application.dtos.equipo_proceso_dto import (
    ClaseProceso,
    EquipoProceso,
)
from src.modules.contadores.application.dtos.solicitud_tablero_siges_dto import (
    SolicitudTableroSigesDto,
)
from src.modules.contadores.application.use_cases._construir_entrada_siges import (
    contexto_proceso_siges,
)
from src.modules.contadores.application.use_cases._construir_estimacion_input import (
    construir_estimacion_input,
)
from src.modules.contadores.application.use_cases._mapear_filas_grilla_siges import (
    agrupar_por_equipo,
)
from src.modules.contadores.application.use_cases._releer_pl_manual import (
    con_pl_releida,
    releer_lecturas_de_siges,
)
from src.modules.contadores.application.use_cases._resolver_resultado_final import (
    decisiones_no_descartadas,
    es_fuente_pendiente,
    resolver_resultado_final,
)
from src.modules.contadores.domain.ports.candidatos_equipo_port import CandidatosEquipoPort
from src.modules.contadores.domain.ports.decisiones_operador_port import DecisionesOperadorPort
from src.modules.contadores.domain.ports.estim_log_port import EstimLogPort
from src.modules.contadores.domain.ports.grilla_estimacion_port import GrillaEstimacionPort
from src.modules.contadores.domain.ports.recesos_port import RecesosPort
from src.modules.contadores.domain.services.estimacion.antiguedad import meses_entre
from src.modules.contadores.domain.services.estimacion.export_csv import (
    ENCABEZADO_CSV,
    FIN_DE_LINEA,
    AuditoriaMaquina,
    FilaExport,
    agrupar_por_maquina,
    linea_csv,
    sanitizar_simbolos,
)
from src.modules.contadores.domain.services.estimacion.resumen_observacion import ClaseObservada
from src.shared.domain.errors import BusinessRuleViolationError

_Decisiones = dict[tuple[int, str], DecisionOperadorDto]


@dataclass(frozen=True, slots=True)
class OpcionesExportCsv:
    """Menú "Exportar CSV ▾" del legacy (Todos / Solo estimados) y el
    `descartar_hasta` vigente del banner de restauración."""

    solo_estimados: bool = False
    descartar_hasta: datetime | None = None


class GenerarExportCsvUseCase:
    """`candidatos` (opcional) relee la Partida/Llegada de una P/L manual por
    `ID_Contador`, como el tablero; sin él se usan las lecturas guardadas."""

    def __init__(
        self,
        gateway: GrillaEstimacionPort,
        decisiones: DecisionesOperadorPort,
        recesos_store: RecesosPort,
        estim_log: EstimLogPort,
        candidatos: CandidatosEquipoPort | None = None,
    ) -> None:
        self._gateway = gateway
        self._decisiones = decisiones
        self._recesos_store = recesos_store
        self._estim_log = estim_log
        self._releer = releer_lecturas_de_siges(candidatos) if candidatos is not None else None

    async def execute(
        self, solicitud: SolicitudTableroSigesDto, opciones: OpcionesExportCsv | None = None
    ) -> str:
        opciones = opciones or OpcionesExportCsv()
        filas_siges = await self._gateway.fetch_grilla(
            solicitud.nro_proceso, solicitud.fecha_objetivo, operador=solicitud.operador
        )
        if not filas_siges:
            return ENCABEZADO_CSV + FIN_DE_LINEA
        ctx = await contexto_proceso_siges(
            filas_siges[0], solicitud.fecha_objetivo, solicitud.id_anexo, self._recesos_store
        )
        decisiones = await self._vigentes(solicitud.nro_proceso, opciones.descartar_hasta)
        filas = [
            fila
            for equipo in agrupar_por_equipo(filas_siges)
            for fila in _filas_de(equipo, ctx, decisiones, opciones.solo_estimados)
        ]
        auditoria = await self._auditoria(solicitud.nro_proceso)
        return _contenido(filas, ctx, auditoria)

    async def _vigentes(self, nro_proceso: int, descartar_hasta: datetime | None) -> _Decisiones:
        todas = await self._decisiones.listar_por_proceso(nro_proceso)
        vigentes = decisiones_no_descartadas(todas, descartar_hasta)
        if self._releer is None:
            return vigentes
        return {c: await con_pl_releida(c, d, self._releer) for c, d in vigentes.items()}

    async def _auditoria(self, nro_proceso: int) -> dict[int, AuditoriaMaquina]:
        resumen = await self._estim_log.resumen_por_maquina(nro_proceso)
        return {
            id_maquina: AuditoriaMaquina(
                sanitizar_simbolos(r.observacion_manual) if r.observacion_manual else None,
                r.id_log_corto or None,
            )
            for id_maquina, r in resumen.items()
        }


def _filas_de(
    equipo: EquipoProceso, ctx: ContextoProcesoDto, decisiones: _Decisiones, solo_estimados: bool
) -> list[FilaExport]:
    filas = (
        _fila_de(equipo, clase, ctx, decisiones.get((equipo.id_maquina, clase.clase)))
        for clase in equipo.clases
    )
    return [f for f in filas if not solo_estimados or _es_estimada(f)]


def _es_estimada(fila: FilaExport) -> bool:
    """`PendienteEstimar && !RequierePendiente` (la fila real no tiene
    decisión restaurada: su resultado es siempre "Sin_Estimar")."""
    fuente = fila.observada.resultado.fuente
    return fuente != "Sin_Estimar" and not es_fuente_pendiente(fuente)


def _fila_de(
    equipo: EquipoProceso,
    clase: ClaseProceso,
    ctx: ContextoProcesoDto,
    decision: DecisionOperadorDto | None,
) -> FilaExport:
    entrada = construir_estimacion_input(equipo, clase, ctx)
    resultado = resolver_resultado_final(entrada, decision).resultado
    ultimo_real = entrada.ultimo_real
    meses = meses_entre(ultimo_real.fecha, ctx.fecha_objetivo) if ultimo_real else None
    return FilaExport(
        equipo.id_maquina,
        clase.clase,
        equipo.nro_serie,
        equipo.empresa,
        equipo.sucursal,
        ClaseObservada(resultado, meses),
    )


def _contenido(
    filas: list[FilaExport], ctx: ContextoProcesoDto, auditoria: dict[int, AuditoriaMaquina]
) -> str:
    lineas = [ENCABEZADO_CSV]
    for grupo in agrupar_por_maquina(filas):
        linea = linea_csv(grupo, ctx.fecha_objetivo, auditoria.get(grupo[0].id_maquina))
        if linea is None:
            raise _sin_contador_principal(grupo[0])
        lineas.append(linea)
    return "".join(linea + FIN_DE_LINEA for linea in lineas)


def _sin_contador_principal(fila: FilaExport) -> BusinessRuleViolationError:
    """v1.7 (`principal = cl10 ?? cl20!`) corta con una excepción ante una
    máquina sin Cl.10 ni Cl.20 y no descarga ningún archivo: acá tampoco se
    genera, pero con un error que dice qué equipo lo impide."""
    return BusinessRuleViolationError(
        f"El equipo {fila.nro_serie} no tiene contador clase 10 ni 20: "
        "no se puede generar el archivo para SiGes",
        code="EXPORT_SIN_CONTADOR_PRINCIPAL",
        details={"id_maquina": fila.id_maquina, "nro_serie": fila.nro_serie},
    )
