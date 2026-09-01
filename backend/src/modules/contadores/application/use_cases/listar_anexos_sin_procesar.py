"""KPI "Anexos sin procesar": el operador se olvidó de generar el proceso de
facturación de un anexo. Ver /home/ivan/.claude/plans/lovely-wandering-lightning.md
para el contexto completo de la decisión de producto.

Invierte a propósito el criterio de `FiltrarPendientesPorPeriodoReal`: allá
"sin cruce no se inventa" y se CONSERVA el pendiente; acá un anexo solo entra
al conteo si Siges lo confirma explícitamente, porque el KPI señala un
olvido concreto de una persona y un falso positivo le hace perder confianza
al número. Si Siges no responde, PROPAGA `ExternalServiceError`: el tile de
Inicio debe mostrar "sin dato", nunca un cero inventado.

`periodo_esperado` es un umbral único por consulta —
`periodo_anterior(periodo_de(hoy))`, un mes de gracia— y NO se deriva de la
fecha de cada evento vencido: el lote de facturación de Siges no corre un
día fijo (verificado 2026-08-31: a veces corre 1-2 días después de fin de
mes), así que atarlo a la fecha exacta de la visita generaría falsos
positivos en las de fin de mes. Mismo mes de gracia que ya usa
`estado_de_periodo` (en_proceso vs. demorado)."""

from dataclasses import dataclass
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
from src.modules.contadores.domain.services.periodos_facturacion import (
    periodo_anterior,
    periodo_de,
)


@dataclass(frozen=True)
class _Obligacion:
    """Lo que el calendario dice de un cliente con arrastre: quién es el
    operador y desde cuándo (para mostrarlo), no el período exacto que le
    corresponde — ese es el mismo umbral para todos."""

    cliente: str
    operador_id: str | None
    fecha_evento: str
    dias_vencido: int


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
        periodo_esperado = periodo_anterior(periodo_de(hoy))
        anexos = _anexos_sin_procesar(snapshot.anexos, indice, periodo_esperado)
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
        actual = directo.get(clave)
        if actual is None or obligacion.dias_vencido > actual.dias_vencido:
            directo[clave] = obligacion
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
    fecha_evento = anotado.event.start[:10]
    dias_vencido = (hoy - date.fromisoformat(fecha_evento)).days
    return _Obligacion(
        cliente=cliente,
        operador_id=anotado.event.operador_id,
        fecha_evento=fecha_evento,
        dias_vencido=dias_vencido,
    )


def _anexos_sin_procesar(
    anexos: list[EstadoProcesoAnexo],
    indice: IndiceNombres[_Obligacion],
    periodo_esperado: str,
) -> list[AnexoSinProcesar]:
    resultado = []
    for anexo in anexos:
        if anexo.ultimo_periodo_procesado is None:
            continue
        if anexo.ultimo_periodo_procesado >= periodo_esperado:
            continue
        obligacion = buscar_por_nombre(anexo.grupo, indice)
        if obligacion is None:
            continue
        resultado.append(_to_dto(anexo, obligacion, periodo_esperado))
    return resultado


def _to_dto(
    anexo: EstadoProcesoAnexo, obligacion: _Obligacion, periodo_esperado: str
) -> AnexoSinProcesar:
    return AnexoSinProcesar(
        id_anexo=anexo.id_anexo,
        anexo=anexo.anexo,
        grupo=anexo.grupo,
        cliente=obligacion.cliente,
        operador_id=obligacion.operador_id,
        fecha_evento=obligacion.fecha_evento,
        dias_vencido=obligacion.dias_vencido,
        periodo_esperado=periodo_esperado,
        ultimo_periodo_procesado=anexo.ultimo_periodo_procesado,
    )
