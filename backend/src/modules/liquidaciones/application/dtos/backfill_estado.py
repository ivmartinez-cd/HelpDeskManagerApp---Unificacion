"""DTO de resultado del backfill de estado de liquidaciones."""

from dataclasses import dataclass, field


@dataclass
class BackfillEstadoPrestadorResultado:
    prestador_id: str
    prestador_nombre: str
    procesadas: int = 0
    actualizadas: int = 0
    saltadas: int = 0      # estado != 'abierta' — respeta trabajo manual de la TL
    sin_match: int = 0     # liquidación local sin correspondencia en AyC (o sin numero)


@dataclass
class BackfillEstadoResultado:
    dry_run: bool
    prestadores: list[BackfillEstadoPrestadorResultado] = field(default_factory=list)
    por_estado_destino: dict[str, int] = field(default_factory=dict)

    @property
    def total_actualizadas(self) -> int:
        return sum(p.actualizadas for p in self.prestadores)

    @property
    def total_saltadas(self) -> int:
        return sum(p.saltadas for p in self.prestadores)
