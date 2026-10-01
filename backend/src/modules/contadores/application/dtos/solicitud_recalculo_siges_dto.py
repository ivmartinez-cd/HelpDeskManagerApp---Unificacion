from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class SolicitudRecalculoSigesDto:
    """Lo que el frontend ya tiene tras elegir Grupo económico → Proceso —
    identifica qué grilla cacheada reusar (agrupado, ARCHITECTURE_GUIDE.md
    §4). La arma `application/use_cases/proyeccion_operador/solicitud_real.py` para el panel
    de candidatos y las acciones del operador (vista previa, forzar, aceptar,
    marcar pendiente), que resuelven la fila con `ConstructorEntradaSiges`."""

    nro_proceso: int
    id_grupo_economico: int
    id_anexo: int
    fecha_objetivo: date
    # Quién carga/opera la grilla: cada operador reusa SU última carga
    # (v1.7: la lista en memoria de su circuito). `None` = sin identificar.
    operador: str | None = None
