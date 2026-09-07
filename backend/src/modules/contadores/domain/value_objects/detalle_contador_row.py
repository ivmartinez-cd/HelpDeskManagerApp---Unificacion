from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class DetalleContadorRow:
    """Una fila del reporte "Detalle de contadores por nro de proceso" —
    a diferencia de `FaltaContadorSourceRow` (que ya viene filtrada a las
    filas con falta de contador para Estimación en 0), acá se trae el
    proceso completo con el flag `falta_contador` calculado por fila, para
    que la pantalla pueda mostrar "todo el proceso" o filtrar a demanda.

    Columnas verificadas 1:1 contra una captura real del reporte legacy
    compartida por el usuario (serie `CNB1R4C0MV`, proceso 99089, Nro_Proceso
    resuelto y contrastado campo por campo — ver
    `detalle_contador_proceso_query.py`). Deliberadamente sin `Backup De` ni
    `CC`: el usuario pidió excluirlas del reporte nuevo.

    `contador_actual` y `tipo` no son un mapeo directo de columna — ver
    docstring de la query."""

    empresa: str
    sucursal: str
    sector: str | None
    modelo: str
    serie: str
    nombre_clase: str | None
    fecha_toma_anterior: date | None
    contador_anterior: int
    fecha_toma_actual: date | None
    contador_actual: int
    impresiones_reales: float
    estado_maquina: str | None
    direccion_ip: str | None
    mascara_ip: str | None
    falta_contador: bool
    tipo: str | None
