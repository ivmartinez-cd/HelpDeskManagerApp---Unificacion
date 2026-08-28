"""Anexo de Impresión con un período de facturación abierto (sin liberar ni
facturar) — el universo del reporte de cierre de contadores, que recrea el
legacy `SiGes/AnexosNoFacturados` acotado a EN PROCESO / DEMORADO /
MES_EN_CURSO (ver `anexos_pendientes_query.py` para la semántica validada
contra Siges)."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class AnexoPendiente:
    id_anexo: int
    anexo: str
    # LEFT JOINs en Siges: contratos/grupos/vendedores pueden faltar en datos
    # históricos sucios — se muestran vacíos, no rompen el reporte.
    grupo: str | None
    contrato: str | None
    id_empresa_admin: int | None
    empresa_admin: str | None
    vendedor: str | None
    moneda: str | None
    moneda_facturacion: str | None
    # Período de facturación abierto, formato YYYYMM (char(6) en Siges).
    periodo: str
    fecha_proceso: date
    # Total en dólares calculado por el proceso abierto (suma de sus
    # subprocesos); 0 si el proceso todavía no corrió la escala.
    importe_usd: Decimal


@dataclass(frozen=True)
class AnexosPendientesSnapshot:
    """Resultado de una consulta con su marca de tiempo — se sirve cacheado
    (TTL en el gateway) y la UI necesita saber de cuándo son los datos."""

    anexos: list[AnexoPendiente]
    consultado_en: datetime
