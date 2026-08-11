"""Puerto de app_settings (key-value crudo; el tipado/defaults vive en
settings_from_raw, no acá)."""

from typing import Protocol


class InsumosSettingsRepository(Protocol):
    async def get_all(self) -> dict[str, str]: ...

    async def set_all(self, values: dict[str, str]) -> None:
        """Upsert por key. No borra las keys que no vengan: app_settings es un
        key-value compartido y un PUT parcial no debe llevarse puestas las demás."""
        ...
