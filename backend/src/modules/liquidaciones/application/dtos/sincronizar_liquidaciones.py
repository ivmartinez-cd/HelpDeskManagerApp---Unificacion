"""DTO de resultado del sync de liquidaciones desde Canal Directo."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SincronizarLiquidacionesResultado:
    creadas: int
    ya_existentes: int
    sin_prestador: int  # prestadores activos sin cd_prestador_id (fuera del sync)
    fallidas: int  # detalle SOAP vacío/fallido: no se crearon, se reintentan
    anuladas: int = 0  # detectadas como anuladas en AyC y eliminadas localmente
    reconciliadas: int = 0  # ya existentes, revisadas contra AyC (con o sin diff)
    estados_actualizados: int = 0  # de las reconciliadas, cuántas pisaron su estado
