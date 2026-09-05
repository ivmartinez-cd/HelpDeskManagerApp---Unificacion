from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class SolicitudTableroSigesDto:
    """Lo que el frontend ya tiene disponible tras elegir Grupo económico →
    Proceso (agrupado en vez de 4 parámetros sueltos, ARCHITECTURE_GUIDE.md
    §4): alcanza para construir el contexto completo sin depender del orden
    de ejecución de la consulta a Siges."""

    nro_proceso: int
    id_grupo_economico: int
    id_anexo: int
    fecha_objetivo: date
