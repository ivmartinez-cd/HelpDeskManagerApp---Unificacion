from dataclasses import dataclass

from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    Coloreo,
    FuenteEstimacion,
    Semaforo,
)


@dataclass(frozen=True, slots=True)
class EstimacionResultado:
    """Salida del motor para un (equipo, clase de contador). `tipo_toma`
    grabado es siempre 14/19/None — nunca 4 (REGLAS_DE_NEGOCIO §4, regla
    dura de grabado)."""

    estim_propuesto: float | None
    impresiones: float | None
    tipo_toma: int | None
    fuente: FuenteEstimacion
    metodo_detalle: str
    requiere_confirmacion: bool
    semaforo: Semaforo
    borde_salto_imposible: bool
    coloreo: Coloreo | None
    nota_operador: str | None
    meses_sin_real_en_alerta: bool
    dias_par_pl: int | None
    ajustado_por_receso: bool
    dias_receso_descontados: int
    dias_proyectados: int | None = None
    par_incluye_t4: bool = False
    t4_sin_revisar: bool = False
    tasa_diaria: float | None = None
