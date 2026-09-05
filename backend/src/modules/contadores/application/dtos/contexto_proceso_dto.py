from dataclasses import dataclass
from datetime import date

from src.modules.contadores.domain.value_objects.estimacion.receso_cliente import RecesoCliente


@dataclass(frozen=True, slots=True)
class ContextoProcesoDto:
    """Datos del proceso de facturación que se está estimando — comunes a
    todos los equipos del tablero (agrupados para no pasarlos sueltos,
    ARCHITECTURE_GUIDE.md §4)."""

    fecha_objetivo: date
    periodo_desde: date
    periodo_hasta: date
    id_grupo_economico: int
    id_anexo: int
    recesos: list[RecesoCliente]
