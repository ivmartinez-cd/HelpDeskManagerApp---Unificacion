from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Saldo:
    """Saldo de vacaciones de un empleado para un ciclo anual.

    `available = total - used - pending` (fórmula del legacy: las PENDING
    restan igual que las APPROVED), con `total = annual + carry_over +
    ajuste_inicial`. `annual` son siempre los días por antigüedad; la
    diferencia con el saldo anotado en la carga inicial va en `ajuste_inicial`.
    """

    annual: int
    carry_over: int
    used: int
    pending: int
    available: int
    cycle_open: bool
    ajuste_inicial: int = 0

    @property
    def total(self) -> int:
        return self.annual + self.carry_over + self.ajuste_inicial
