"""Auditoría de las acciones del operador sobre el tablero de Proyección — un
INSERT append-only por acción (`GrillaEstimacion.EscribirAudit` del legacy),
en paralelo a la decisión vigente que guarda cada endpoint
(`DecisionesOperadorPort`). La vista previa de una P/L no se audita: el
legacy audita recién al aceptar. `accion` usa los nombres de `AccionAudit`
del legacy.

Mismos datos que `Estim_Log`: contador anterior (`?? 0`), propuesto (`?? 0`;
al marcar pendiente, el anterior), tipo de toma (`?? 14`), fuente (con el
nombre del legacy: una fila pendiente es `Sin_Estimar`),
`Aceptado` (falso solo al marcar pendiente) y la composición del estimador
del Paquete 10.A (método, parque, P/L, etiqueta) en `detalle`."""

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from src.modules.contadores.application.dtos.decision_operador_dto import (
    LecturaElegidaDto,
    ParPartidaLlegadaDto,
)
from src.modules.contadores.application.use_cases._resolver_resultado_final import (
    es_fuente_pendiente,
)
from src.modules.contadores.application.use_cases.proyeccion_operador.dependencias import (
    OperadorProyeccion,
)
from src.modules.contadores.domain.ports.estim_log_port import EntradaEstimLog, EstimLogPort
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)

# `TipoToma.Estimado`: lo que el legacy audita cuando la fila no sugiere tipo.
_TIPO_TOMA_ESTIMADO = 14
# `FuenteEstimacion.Sin_Estimar`: la fuente de una fila `RequierePendiente`
# del legacy (del motor o marcada por el operador, `ConstruirPendiente`); el
# motor de HDM la representa como "Pendiente".
_FUENTE_SIN_ESTIMAR = "Sin_Estimar"


@dataclass(frozen=True, slots=True)
class RegistroAccion:
    """`nro_proceso` es el que mandó el frontend (`None` en el modo ejemplo,
    para no mezclar su auditoría con la de un proceso real). `resultado` es
    lo que quedó en la fila (o lo que mostraba, al aceptar la sugerencia).
    `contador_propuesto` pisa el del resultado (marcar pendiente)."""

    id_maquina: int
    clase: str
    accion: str
    nro_proceso: int | None
    fecha_objetivo: date | None
    observacion: str | None
    resultado: EstimacionResultado
    contador_anterior: float
    contador_propuesto: float | None = None
    aceptado: bool = True
    detalle: dict[str, Any] = field(default_factory=dict)


async def registrar_accion(
    estim_log: EstimLogPort, operador: OperadorProyeccion, registro: RegistroAccion
) -> None:
    entrada = EntradaEstimLog(
        operador_user_id=operador.user_id,
        operador_email=operador.email,
        id_maquina=registro.id_maquina,
        clase=registro.clase,
        accion=registro.accion,
        fecha_objetivo=registro.fecha_objetivo,
        nro_proceso=registro.nro_proceso,
        observacion=registro.observacion,
        **campos_resultado(registro),
    )
    await estim_log.registrar(entrada)


def detalle_pl(par: ParPartidaLlegadaDto) -> dict[str, Any]:
    """`PartidaIdContador`/`LlegadaIdContador` del legacy, más los valores
    elegidos (para leer el log sin ir a Siges)."""
    return {**_lectura("partida", par.partida), **_lectura("llegada", par.llegada)}


def campos_resultado(registro: RegistroAccion) -> dict[str, Any]:
    r = registro.resultado
    propuesto = registro.contador_propuesto
    if propuesto is None:
        propuesto = r.estim_propuesto if r.estim_propuesto is not None else 0.0
    detalle = {**registro.detalle, "aceptado": registro.aceptado}
    return {
        "contador_anterior": registro.contador_anterior,
        "contador_propuesto": propuesto,
        "tipo_toma_grabado": r.tipo_toma if r.tipo_toma is not None else _TIPO_TOMA_ESTIMADO,
        "fuente": _FUENTE_SIN_ESTIMAR if es_fuente_pendiente(r.fuente) else r.fuente,
        "metodo_detalle": r.metodo_detalle,
        "detalle": {**detalle, **_composicion(r)},
    }


def _composicion(r: EstimacionResultado) -> dict[str, Any]:
    """Paquete 10.A (`MetodoEstimacion`, `N_Parque`… `EtiquetaNivel`).
    `detalle_calculo` puede pasar los 200 caracteres de `metodo_detalle`."""
    parque = r.detalle_parque
    return {
        "metodo": r.metodo,
        "n_parque": parque.n_equipos if parque else None,
        "n_descartados": parque.n_descartados if parque else None,
        "mediana_cruda": parque.mediana_cruda if parque else None,
        "media_cruda": parque.media_cruda if parque else None,
        "dias_par_pl": r.dias_par_pl,
        "promedio_diario": r.tasa_diaria,
        "dias_extrapolados": r.dias_proyectados,
        "etiqueta_nivel": r.etiqueta_nivel or None,
        "marcas": sorted(r.marcas),
        "detalle_calculo": r.detalle_calculo,
    }


def _lectura(prefijo: str, lectura: LecturaElegidaDto) -> dict[str, Any]:
    return {
        f"{prefijo}_id_contador": lectura.id_contador,
        f"{prefijo}_fecha": lectura.fecha.isoformat(),
        f"{prefijo}_valor": lectura.valor,
        f"{prefijo}_tipo_toma": lectura.tipo_toma,
    }
