import re
from dataclasses import dataclass
from uuid import UUID

from src.modules.auth.domain.errors import InvalidDashboardPrefsError

VISTAS_VALIDAS = frozenset({"hoy", "seguimiento"})
VISTA_DEFAULT = "hoy"
# Ids de card del registro del frontend (`dashboard-registry.ts`): slug corto.
_CARD_ID = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
MAX_HIDDEN_CARDS = 32


@dataclass(frozen=True, slots=True)
class DashboardPrefs:
    """Preferencias personales del dashboard de Inicio: qué paneles oculta el
    usuario y con qué vista abre. Es un dato del propio usuario (como las
    visitas de rutas, ADR-028): se valida acá por forma, no contra el
    catálogo de cards — el frontend ignora ids que ya no existan."""

    user_id: UUID
    hidden_cards: tuple[str, ...]
    initial_view: str

    def __post_init__(self) -> None:
        if self.initial_view not in VISTAS_VALIDAS:
            raise InvalidDashboardPrefsError(f"vista inicial desconocida: {self.initial_view!r}")
        if len(self.hidden_cards) > MAX_HIDDEN_CARDS:
            raise InvalidDashboardPrefsError(
                f"demasiados paneles ocultos ({len(self.hidden_cards)} > {MAX_HIDDEN_CARDS})"
            )
        for card in self.hidden_cards:
            if not _CARD_ID.match(card):
                raise InvalidDashboardPrefsError(f"id de panel inválido: {card!r}")
        if len(set(self.hidden_cards)) != len(self.hidden_cards):
            raise InvalidDashboardPrefsError("paneles ocultos repetidos")

    @classmethod
    def default(cls, user_id: UUID) -> "DashboardPrefs":
        return cls(user_id=user_id, hidden_cards=(), initial_view=VISTA_DEFAULT)
