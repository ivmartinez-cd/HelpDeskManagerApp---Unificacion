"""Funciones por usuario (ADR-032): reemplazo atómico e idempotente + auditoría."""

import uuid

import pytest

from src.modules.auth.application.use_cases.features import (
    GetUserFeatures,
    GetUserFeaturesDependencies,
    ReplaceUserFeatures,
    ReplaceUserFeaturesDependencies,
)
from src.modules.auth.domain.errors import UnknownFeatureError, UserNotFoundError
from src.modules.auth.domain.value_objects.feature_set import FeatureSet
from src.shared.domain.value_objects.feature_key import FeatureKey
from tests.unit.application.auth.fakes import (
    FakeFeatureCatalogRepository,
    FakeFeatureGrantRepository,
    FakePermissionAuditRepository,
    FakeUserRepository,
    make_user,
)

_COB = FeatureKey("contadores-coberturas")
_ANEXOS = FeatureKey("contadores-anexos")


def _users_with_target() -> tuple[FakeUserRepository, uuid.UUID]:
    users = FakeUserRepository()
    user = make_user()
    users.rows[user.id] = user
    return users, user.id


def _deps(
    users: FakeUserRepository,
    repo: FakeFeatureGrantRepository,
    audit: FakePermissionAuditRepository,
) -> ReplaceUserFeaturesDependencies:
    return ReplaceUserFeaturesDependencies(
        users=users,
        features=repo,
        catalog=FakeFeatureCatalogRepository({_COB.value, _ANEXOS.value}),
        audit=audit,
    )


async def test_replace_escribe_y_audita_solo_el_diff() -> None:
    repo, audit = FakeFeatureGrantRepository(), FakePermissionAuditRepository()
    users, target = _users_with_target()
    actor = uuid.uuid4()
    repo.by_user[target] = FeatureSet(frozenset({_COB}))

    await ReplaceUserFeatures(_deps(users, repo, audit)).execute(
        target_user_id=target, desired=FeatureSet(frozenset({_ANEXOS})), actor_user_id=actor
    )

    assert repo.by_user[target].granted == frozenset({_ANEXOS})
    assert audit.feature_diffs == [(actor, target, frozenset({_ANEXOS}), frozenset({_COB}))]


async def test_replace_sin_cambios_no_escribe_ni_audita() -> None:
    repo, audit = FakeFeatureGrantRepository(), FakePermissionAuditRepository()
    users, target = _users_with_target()
    repo.by_user[target] = FeatureSet(frozenset({_COB}))

    await ReplaceUserFeatures(_deps(users, repo, audit)).execute(
        target_user_id=target, desired=FeatureSet(frozenset({_COB})), actor_user_id=uuid.uuid4()
    )

    assert repo.replaced == []
    assert audit.feature_diffs == []


async def test_replace_a_usuario_inexistente_es_not_found() -> None:
    repo, audit = FakeFeatureGrantRepository(), FakePermissionAuditRepository()

    with pytest.raises(UserNotFoundError):
        await ReplaceUserFeatures(_deps(FakeUserRepository(), repo, audit)).execute(
            target_user_id=uuid.uuid4(),
            desired=FeatureSet(frozenset({_COB})),
            actor_user_id=uuid.uuid4(),
        )

    assert repo.replaced == []


async def test_replace_con_funcion_fuera_del_catalogo_es_validacion_y_no_escribe() -> None:
    repo, audit = FakeFeatureGrantRepository(), FakePermissionAuditRepository()
    users, target = _users_with_target()

    with pytest.raises(UnknownFeatureError):
        await ReplaceUserFeatures(_deps(users, repo, audit)).execute(
            target_user_id=target,
            desired=FeatureSet(frozenset({_COB, FeatureKey("no-existe")})),
            actor_user_id=uuid.uuid4(),
        )

    assert repo.replaced == []
    assert audit.feature_diffs == []


async def test_get_devuelve_vacio_para_usuario_sin_grants() -> None:
    users, target = _users_with_target()
    repo = FakeFeatureGrantRepository()

    features = await GetUserFeatures(
        GetUserFeaturesDependencies(users=users, features=repo)
    ).execute(target)

    assert features.granted == frozenset()
    assert not features.has(_COB)


async def test_get_de_usuario_inexistente_es_not_found() -> None:
    deps = GetUserFeaturesDependencies(
        users=FakeUserRepository(), features=FakeFeatureGrantRepository()
    )

    with pytest.raises(UserNotFoundError):
        await GetUserFeatures(deps).execute(uuid.uuid4())
