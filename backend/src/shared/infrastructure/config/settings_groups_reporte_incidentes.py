"""Grupo de settings del módulo reporte_incidentes (archivo propio para no seguir
agrandando `settings_groups_operativos.py`)."""

from pydantic import Field
from pydantic_settings import BaseSettings


class ReporteIncidentesSettings(BaseSettings):
    """Reporte ejecutivo de incidentes: lecturas a wsAyC y tipificación con IA."""

    # Cuántos incidentes pedirle a `getTopIncidents` por cada mes hacia atrás
    # (no filtra por fecha: devuelve los N más recientes). Default del código
    # legacy (`SOAP_TEST_INCIDENT_LIMIT`).
    reporte_incidentes_limite_por_mes: int = Field(default=500, ge=1)
    # Llamadas SOAP en paralelo (un mes de N incidentes cuesta 1 + 2×N).
    reporte_incidentes_concurrencia_soap: int = Field(default=4, ge=1)
    # Vida de la caché en memoria de las respuestas de wsAyC (legacy: 15 min).
    reporte_incidentes_cache_ttl_segundos: int = Field(default=900, ge=0)
