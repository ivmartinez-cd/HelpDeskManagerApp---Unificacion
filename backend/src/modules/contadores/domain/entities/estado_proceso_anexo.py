"""Estado real de proceso de facturación por anexo de Impresión en Siges:
para cada anexo activo, el último `PeriodoFacturacion` (YYYYMM) que llegó a
tener `Nro_Proceso` asignado. `Nro_Proceso` nunca es NULL en una fila
existente de `Factura_Anexo` (verificado 2026-08-31, 0 de 98.508 filas): la
señal de "nunca se generó el proceso" es la AUSENCIA total de fila para ese
período, no un valor vacío — por eso acá alcanza con saber cuál fue el
último período procesado, o `None` si el anexo no tiene ningún historial."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EstadoProcesoAnexo:
    id_anexo: int
    anexo: str
    grupo: str
    # Último PeriodoFacturacion (YYYYMM) con Nro_Proceso asignado. None si el
    # anexo nunca tuvo ningún proceso (alta reciente o factura por otro
    # circuito) — sin historial no hay prueba de olvido, se descarta aparte.
    ultimo_periodo_procesado: str | None


@dataclass(frozen=True)
class EstadoProcesoAnexosSnapshot:
    """Universo completo de anexos de Impresión activos — no solo los sin
    procesar. Se sirve cacheado (TTL en el gateway)."""

    anexos: list[EstadoProcesoAnexo]
    consultado_en: datetime
