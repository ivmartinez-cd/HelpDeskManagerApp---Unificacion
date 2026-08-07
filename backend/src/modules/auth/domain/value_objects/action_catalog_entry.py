from dataclasses import dataclass

from src.shared.domain.value_objects.action_key import ActionKey


@dataclass(frozen=True, slots=True)
class ActionCatalogEntry:
    key: ActionKey
    label: str
