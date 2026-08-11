"""Puerto de app_settings (key-value crudo; el tipado/defaults vive en
settings_from_raw, no acá)."""

from typing import Protocol


class InsumosSettingsRepository(Protocol):
    async def get_all(self) -> dict[str, str]: ...
