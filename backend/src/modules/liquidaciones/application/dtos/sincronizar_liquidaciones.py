"""DTO de resultado del sync de liquidaciones desde Canal Directo."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SincronizarLiquidacionesResultado:
    creadas: int
    ya_existentes: int
    sin_prestador: int  # prestadores activos sin cd_prestador_id (fuera del sync)
    fallidas: int  # detalle SOAP vacío/fallido: no se crearon, se reintentan
