"""Preliquidación importada de un prestador — liquidaciones.

`periodo` es "YYYY-MM". `tipo_liquidacion` distingue liquidaciones regulares de las que
se facturan a $0,01 (Pre-Correctivo, Centro Cívico San Juan — RN003/RN009 del legacy) o
depósito, cada una con su propia numeración/archivo. `estado` es el workflow de revisión
de la Team Leader — TRIGGERED→...→cerrada, cambiado manualmente vía la pantalla de
detalle, no por ningún proceso automático (sin integración externa en esta migración,
ver §6 de `LIQUIDACION_PRESTADORES_CARACTERIZACION.md`).
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

TIPO_REGULAR = "regular"
TIPO_PRECO = "preco"
TIPO_CC = "cc"
TIPO_DEPOSITO = "deposito"

ESTADO_ABIERTA = "abierta"
ESTADO_PRELIQUIDADA = "preliquidada"
ESTADO_RECIBIDA = "recibida"
ESTADO_OBSERVADA = "observada"
ESTADO_APROBADA = "aprobada"
ESTADO_CERRADA = "cerrada"


@dataclass(frozen=True)
class Liquidacion:
    id: uuid.UUID
    prestador_id: uuid.UUID
    numero_liquidacion: str | None
    periodo: str
    tipo_liquidacion: str
    nombre_archivo: str | None
    fecha_importacion: datetime
    estado: str
    total_incidentes: int
    total_alertas: int
    total_importe: float
    concepto_extra: str | None = None
    monto_extra: float | None = None
    numero_factura: str | None = None
    factura_pdf_url: str | None = None
