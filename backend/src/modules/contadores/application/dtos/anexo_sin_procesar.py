from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AnexoSinProcesar:
    """Un anexo activo de Impresión sin `Nro_Proceso` del último período
    cerrado con seguridad, de un cliente con evento vencido en el calendario
    de Gestión — ver `listar_anexos_sin_procesar.py`."""

    id_anexo: int
    anexo: str
    grupo: str
    cliente: str
    """Texto libre de Gestión que cruzó contra `grupo` (puede diferir en
    forma: acentos, alias manual, etc.)."""
    operador_id: str | None
    fecha_evento: str
    """Fecha (YYYY-MM-DD) del evento vencido más antiguo del cliente — la
    señal más fuerte de hace cuánto viene el arrastre."""
    dias_vencido: int
    periodo_esperado: str
    ultimo_periodo_procesado: str | None


@dataclass(frozen=True)
class ResultadoAnexosSinProcesar:
    anexos: list[AnexoSinProcesar]
    consultado_en: datetime


@dataclass(frozen=True)
class ResumenAnexosSinProcesar:
    """KPI de Inicio: `clientes` es el número grande (grupos económicos
    distintos con al menos un anexo sin procesar) y `anexos` el contexto."""

    clientes: int
    anexos: int
    consultado_en: datetime
