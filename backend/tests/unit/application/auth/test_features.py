"""Funciones por usuario (ADR-032): reemplazo atómico e idempotente + auditoría."""

import uuid

from src.modules.auth.application.use_cases.features import (
    GetUserFeatures,
    GetUserFeaturesDependencies,
    ReplaceUserFeatures,
    ReplaceUserFeaturesDependencies,
)
from src.modules.auth.domain.value_objects.feature_set import FeatureSet
from src.shared.domain.value_objects.feature_key import FeatureKey
from tests.unit.application.auth.fakes import (
    FakeFeatureGrantRepository,
    FakePermissionAuditRepository,
)

_COB = FeatureKey("contadores-coberturas")
_ANEXOS = FeatureKey("contadores-anexos")


async def test_replace_escribe_y_audita_solo_el_diff() -> None:
    repo, audit = FakeFeatureGrantRepository(), FakePermissionAuditRepository()
    target, actor = uuid.uuid4(), uuid.uuid4()
    repo.by_user[target] = FeatureSet(frozenset({_COB}))

    await ReplaceUserFeatures(ReplaceUserFeaturesDependencies(features=repo, audit=audit)).execute(
        target_user_id=target, desired=FeatureSet(frozenset({_ANEXOS})), actor_user_id=actor
    )

    assert repo.by_user[target].granted == frozenset({_ANEXOS})
    assert audit.feature_diffs == [(actor, target, frozenset({_ANEXOS}), frozenset({_COB}))]


async def test_replace_sin_cambios_no_escribe_ni_audita() -> None:
    repo, audit = FakeFeatureGrantRepository(), FakePermissionAuditRepository()
    target = uuid.uuid4()
    repo.by_user[target] = FeatureSet(frozenset({_COB}))

    await ReplaceUserFeatures(ReplaceUserFeaturesDependencies(features=repo, audit=audit)).execute(
        target_user_id=target, desired=FeatureSet(frozenset({_COB})), actor_user_id=uuid.uuid4()
    )

    assert repo.replaced == []
    assert audit.feature_diffs == []


async def test_get_devuelve_vacio_para_desconocido() -> None:
    repo = FakeFeatureGrantRepository()
    features = await GetUserFeatures(GetUserFeaturesDependencies(features=repo)).execute(
        uuid.uuid4()
    )
    assert features.granted == frozenset()
    assert not features.has(_COB)
