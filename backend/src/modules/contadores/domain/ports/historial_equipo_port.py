from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LecturaHistorialSiges:
    """Una fila cruda de `GetHistorialEquipo.sql` (MODELO_DE_DATOS.md §3.6),
    antes de enriquecer con Delta/clasificación (`historial_equipo.py`)."""

    fecha: date
    valor: float
    id_tipo_toma: int
    tipo_toma_desc: str
    para_facturar: bool
    fc_nro_proceso: int | None
    fc_periodo_hasta: date | None
    fc_impresiones: float | None
    fc_periodo_facturacion: str | None
    id_factura: int
    snap_id_empresa: int | None
    snap_id_sucursal: int | None
    snap_id_anexo: int | None


class HistorialEquipoPort(Protocol):
    """Puerto de solo lectura contra Siges para la línea de tiempo de un
    equipo (MODELO_DE_DATOS.md §3.6, `DrillDownModal` legacy)."""

    async def fetch_historial(
        self, id_maquina: int, id_clase_contador: int, desde: date
    ) -> list[LecturaHistorialSiges]:
        """Todas las lecturas desde `desde`, más recientes primero (mismo
        orden que `GetHistorialEquipo.sql`: FechaTomaContador DESC)."""
        ...
