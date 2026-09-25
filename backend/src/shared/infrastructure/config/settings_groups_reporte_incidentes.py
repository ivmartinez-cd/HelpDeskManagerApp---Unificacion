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

    # Tipificación con IA (Gemini). Sin clave, los casos sin tipificación guardada
    # quedan "Pendiente de revision" y el botón de tipificar responde 502 claro.
    # `GEMINI_API_KEY` es la variable que ya declara `.env.example`.
    gemini_api_key: str = ""
    # Modelos propios del reporte (no `GEMINI_MODEL`, que el .env usa para otra cosa).
    # Mismos defaults que el legacy.
    reporte_incidentes_gemini_modelo: str = "gemini-3.5-flash"
    reporte_incidentes_gemini_modelo_fallback: str = "gemini-3.5-flash-lite"
    # 0 (sin thinking) da 400 en los modelos 3.x; 1 es el mínimo aceptado.
    reporte_incidentes_gemini_thinking_budget: int = Field(default=1, ge=1)
    reporte_incidentes_gemini_timeout_segundos: float = Field(default=120.0, gt=0)
    # Casos por pedido a la IA y pedidos en paralelo (legacy: 25 y 4).
    reporte_incidentes_ia_lote: int = Field(default=25, ge=1)
    reporte_incidentes_ia_concurrencia: int = Field(default=4, ge=1)
    # USD por millón de tokens, solo para informar el costo de cada corrida.
    reporte_incidentes_precio_entrada_por_millon: float = 0.3
    reporte_incidentes_precio_salida_por_millon: float = 2.5
