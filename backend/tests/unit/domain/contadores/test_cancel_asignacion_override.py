import uuid
from unittest.mock import AsyncMock

import pytest

from src.modules.contadores.application.use_cases.cancel_asignacion_override import (
    CancelAsignacionOverride,
    CancelAsignacionOverrideDependencies,
)
from src.modules.contadores.domain.errors import AsignacionOverrideNotFoundError


@pytest.mark.asyncio
async def test_cancela_un_override_existente() -> None:
    overrides = AsyncMock()
    overrides.get_by_id.return_value = object()
    override_id = uuid.uuid4()

    await CancelAsignacionOverride(
        CancelAsignacionOverrideDependencies(overrides=overrides)
    ).execute(override_id)

    overrides.cancelar.assert_awaited_once_with(override_id)


@pytest.mark.asyncio
async def test_cancelar_inexistente_lanza_not_found() -> None:
    overrides = AsyncMock()
    overrides.get_by_id.return_value = None

    with pytest.raises(AsignacionOverrideNotFoundError):
        await CancelAsignacionOverride(
            CancelAsignacionOverrideDependencies(overrides=overrides)
        ).execute(uuid.uuid4())
