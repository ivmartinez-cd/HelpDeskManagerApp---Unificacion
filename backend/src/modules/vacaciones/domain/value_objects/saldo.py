from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Saldo:
    """Saldo de vacaciones de un empleado para un ciclo anual.

    `available = (annual + carry_over) - used - pending` (fórmula del legacy:
    las PENDING restan igual que las APPROVED).
    """

    annual: int
    carry_over: int
    used: int
    pending: int
    available: int
    cycle_open: bool
