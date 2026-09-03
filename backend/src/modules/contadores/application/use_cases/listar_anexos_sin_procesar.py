"""KPI "Anexos sin procesar": el operador se olvidó de generar el proceso de
facturación de un anexo. Ver /home/ivan/.claude/plans/lovely-wandering-lightning.md
para el contexto completo de la decisión de producto.

Invierte a propósito el criterio de `FiltrarPendientesPorPeriodoReal`: allá
"sin cruce no se inventa" y se CONSERVA el pendiente; acá un anexo solo entra
al conteo si Siges lo confirma explícitamente, porque el KPI señala un
olvido concreto de una persona y un falso positivo le hace perder confianza
al número. Si Siges no responde, PROPAGA `ExternalServiceError`: el tile de
Inicio debe mostrar "sin dato", nunca un cero inventado.

`periodo_esperado` se deriva de la FECHA DE CADA EVENTO vencido
(`periodo_de(fecha_evento)`, ciclo que rota el día DIA_CIERRE), no de un
umbral único por consulta. La ventana de backlog (30 días) siempre cruza un
día 20, así que un umbral global falla de un lado o del otro: con
`periodo_de(hoy)` cada día 21 acusaría a clientes cuya visita del período
nuevo todavía no ocurrió; con `periodo_anterior(periodo_de(hoy))` (lo que
había hasta el 2026-09-03) el KPI daba 0 todo el mes — el 3/9 el período
que se estaba procesando era 202608 y el umbral pedía 202607, que ya tenía
todo el mundo. Verificado contra Factura_Anexo el 2026-09-03: los procesos
de un período YYYYMM se generan desde el ~11 de ese mes hasta los primeros
días del siguiente (202608: 11/8 → 3/9), así que para una visita posterior
al día 20 el proceso de su período ya está disponible el mismo día — no hay
falso positivo por corrimiento del lote. Si un cliente tiene varios eventos
vencidos, se exige el período MÁS NUEVO (el olvido más reciente también
cuenta) y se muestra la fecha del más antiguo (la señal más fuerte de
arrastre).

Caso real 2026-09-03: OCA (`COD36CDSI00619/A`) tenía 12 máquinas ligadas,
las 12 "De Baja" — 0 activas en Siges. Sin parque vigente no hay nada que
facturar, así que un `maquinas_activas == 0` se descarta igual que "sin
historial": no es un olvido del operador, es un anexo que debió cerrarse
junto con su parque."""

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime

from src.modules.contadores.application.dtos.anexo_sin_procesar import (
    AnexoSinProcesar,
    ResultadoAnexosSinProcesar,
)
from src.modules.contadores.application.dtos.calendar_event_anotado import CalendarEventAnotado
from src.modules.contadores.domain.entities.estado_proceso_anexo import EstadoProcesoAnexo
from src.modules.contadores.domain.ports.estado_proceso_anexos_port import (
    EstadoProcesoAnexosPort,
)
from src.modules.contadores.domain.services.cliente_matcher import (
    ALIAS_CLIENTE_GRUPO_NORM,
    IndiceNombres,
    buscar_por_nombre,
    normalizar_nombre,
)
from src.modules.contadores.domain.services.periodos_facturacion import periodo_de


@dataclass(frozen=True)
class _Obligacion:
    """Lo que el calendario dice de un cliente con arrastre: qué período le
    tocaba procesar, quién es el operador y desde cuándo viene el arrastre."""

    cliente: str
    operador_id: str | None
    fecha_evento: str
    dias_vencido: int
    periodo_esperado: str


class ListarAnexosSinProcesar:
    def __init__(self, port: EstadoProcesoAnexosPort) -> None:
        self._port = port

    async def execute(
        self, pendientes: list[CalendarEventAnotado], *, hoy: date
    ) -> ResultadoAnexosSinProcesar:
        indice = _indice_obligaciones(pendientes, hoy=hoy)
        if not indice.exacto:
            return ResultadoAnexosSinProcesar(anexos=[], consultado_en=datetime.now(UTC))
        snapshot = await self._port.list_estado()  # sin try/except: propaga
        anexos = _anexos_sin_procesar(snapshot.anexos, indice)
        anexos.sort(key=lambda a: a.dias_vencido, reverse=True)
        return ResultadoAnexosSinProcesar(anexos=anexos, consultado_en=snapshot.consultado_en)


def _indice_obligaciones(
    pendientes: list[CalendarEventAnotado], *, hoy: date
) -> IndiceNombres[_Obligacion]:
    directo: dict[str, _Obligacion] = {}
    for anotado in pendientes:
        obligacion = _obligacion_de(anotado, hoy=hoy)
        if obligacion is None:
            continue
        clave = normalizar_nombre(obligacion.cliente)
        directo[clave] = _fusionar(directo.get(clave), obligacion)
    via_alias = {
        ALIAS_CLIENTE_GRUPO_NORM[clave]: obligacion
        for clave, obligacion in directo.items()
        if clave in ALIAS_CLIENTE_GRUPO_NORM
    }
    return IndiceNombres({**directo, **via_alias})


def _obligacion_de(anotado: CalendarEventAnotado, *, hoy: date) -> _Obligacion | None:
    cliente = anotado.event.cliente
    if not cliente:
        return None
    fecha_evento = date.fromisoformat(anotado.event.start[:10])
    return _Obligacion(
        cliente=cliente,
        operador_id=anotado.event.operador_id,
        fecha_evento=fecha_evento.isoformat(),
        dias_vencido=(hoy - fecha_evento).days,
        periodo_esperado=periodo_de(fecha_evento),
    )


def _fusionar(actual: _Obligacion | None, nueva: _Obligacion) -> _Obligacion:
    """Varios eventos vencidos del mismo cliente: se muestra el más antiguo y
    se exige el período más nuevo entre todos (ver docstring del módulo)."""
    if actual is None:
        return nueva
    mas_antigua = nueva if nueva.dias_vencido > actual.dias_vencido else actual
    return replace(
        mas_antigua,
        periodo_esperado=max(actual.periodo_esperado, nueva.periodo_esperado),
    )


def _anexos_sin_procesar(
    anexos: list[EstadoProcesoAnexo], indice: IndiceNombres[_Obligacion]
) -> list[AnexoSinProcesar]:
    resultado = []
    for anexo in anexos:
        if anexo.ultimo_periodo_procesado is None:
            continue
        if anexo.maquinas_activas == 0:
            continue
        obligacion = buscar_por_nombre(anexo.grupo, indice)
        if obligacion is None:
            continue
        if anexo.ultimo_periodo_procesado >= obligacion.periodo_esperado:
            continue
        resultado.append(_to_dto(anexo, obligacion))
    return resultado


def _to_dto(anexo: EstadoProcesoAnexo, obligacion: _Obligacion) -> AnexoSinProcesar:
    return AnexoSinProcesar(
        id_anexo=anexo.id_anexo,
        anexo=anexo.anexo,
        grupo=anexo.grupo,
        cliente=obligacion.cliente,
        operador_id=obligacion.operador_id,
        fecha_evento=obligacion.fecha_evento,
        dias_vencido=obligacion.dias_vencido,
        periodo_esperado=obligacion.periodo_esperado,
        ultimo_periodo_procesado=anexo.ultimo_periodo_procesado,
    )
