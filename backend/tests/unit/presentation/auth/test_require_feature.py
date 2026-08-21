"""`require_feature` / `tiene_feature` (ADR-032): fail-closed por clave,
superadmin implícito."""

import uuid

import pytest

from src.modules.auth.application.dtos.results import Identity, UserView
from src.modules.auth.domain.errors import ForbiddenError
from src.modules.auth.presentation.dependencies.features import require_feature, tiene_feature
from src.shared.domain.value_objects.feature_key import FeatureKey

_ANEXOS = FeatureKey("contadores-anexos")


def _identity(*features: str, superadmin: bool = False) -> Identity:
    return Identity(
        user=UserView(
            id=uuid.uuid4(),
            email="op@example.com",
            full_name="Op",
            is_superadmin=superadmin,
            color=None,
        ),
        permissions=frozenset(),
        session_id=uuid.uuid4(),
        features=frozenset(features),
    )


async def test_sin_la_funcion_es_403() -> None:
    with pytest.raises(ForbiddenError):
        await require_feature(_ANEXOS)(identity=_identity("contadores-coberturas"))


async def test_con_la_funcion_pasa() -> None:
    identity = _identity("contadores-anexos")
    assert await require_feature(_ANEXOS)(identity=identity) is identity


async def test_superadmin_la_tiene_implicita() -> None:
    identity = _identity(superadmin=True)
    assert await require_feature(_ANEXOS)(identity=identity) is identity
    assert tiene_feature(identity, _ANEXOS)
    assert not tiene_feature(_identity(), _ANEXOS)
