from pydantic import BaseModel, ConfigDict, Field

from src.modules.auth.domain.entities.dashboard_prefs import MAX_HIDDEN_CARDS, DashboardPrefs


class DashboardPrefsBody(BaseModel):
    """Solo tipo y tamaño acá; la regla (ids slug, vista válida, sin repetidos)
    vive en la entidad `DashboardPrefs`."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    hidden_cards: list[str] = Field(
        alias="hiddenCards", default_factory=list, max_length=MAX_HIDDEN_CARDS
    )
    initial_view: str = Field(alias="initialView", min_length=1, max_length=16)


class DashboardPrefsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    hidden_cards: list[str] = Field(serialization_alias="hiddenCards")
    initial_view: str = Field(serialization_alias="initialView")

    @classmethod
    def from_domain(cls, prefs: DashboardPrefs) -> "DashboardPrefsResponse":
        return cls(hidden_cards=list(prefs.hidden_cards), initial_view=prefs.initial_view)
