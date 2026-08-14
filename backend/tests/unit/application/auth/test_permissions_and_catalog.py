"""ReplaceUserPermissions, ListVisibleModules y los passthrough de catálogo."""

import uuid

import pytest

from src.modules.auth.application.use_cases.get_user_permissions import (
    GetUserPermissions,
    GetUserPermissionsDependencies,
)
from src.modules.auth.application.use_cases.list_action_catalog import (
    ListActionCatalog,
    ListActionCatalogDependencies,
)
from src.modules.auth.application.use_cases.list_module_catalog import (
    ListModuleCatalog,
    ListModuleCatalogDependencies,
)
from src.modules.auth.application.use_cases.list_visible_modules import (
    ListVisibleModules,
    ListVisibleModulesDependencies,
)
from src.modules.auth.application.use_cases.replace_user_permissions import (
    ReplaceUserPermissions,
    ReplaceUserPermissionsDependencies,
)
from src.modules.auth.domain.errors import CannotDemoteSelfError
from src.modules.auth.domain.value_objects.action_catalog_entry import ActionCatalogEntry
from src.modules.auth.domain.value_objects.module_catalog_entry import ModuleCatalogEntry
from src.modules.auth.domain.value_objects.permission_set import PermissionSet
from src.modules.auth.domain.well_known_permissions import MANAGE_ADMIN
from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission
from tests.unit.application.auth.fakes import (
    FakePermissionAuditRepository,
    FakePermissionRepository,
)

_VER_INSUMOS = Permission(ModuleKey("insumos"), ActionKey("view"))
_VER_TURNOS = Permission(ModuleKey("turnos"), ActionKey("view"))


def _replace_deps(
    permissions: FakePermissionRepository, audit: FakePermissionAuditRepository
) -> ReplaceUserPermissionsDependencies:
    return ReplaceUserPermissionsDependencies(permissions=permissions, audit=audit)


async def test_no_podes_sacarte_a_vos_mismo_admin_manage() -> None:
    actor = uuid.uuid4()

    with pytest.raises(CannotDemoteSelfError):
        await ReplaceUserPermissions(
            _replace_deps(FakePermissionRepository(), FakePermissionAuditRepository())
        ).execute(
            target_user_id=actor,
            desired=PermissionSet(granted=frozenset({_VER_INSUMOS})),
            actor_user_id=actor,
        )


async def test_sin_diff_no_escribe_ni_audita() -> None:
    permissions = FakePermissionRepository()
    audit = FakePermissionAuditRepository()
    target = uuid.uuid4()
    actual = PermissionSet(granted=frozenset({_VER_INSUMOS}))
    permissions.by_user[target] = actual

    await ReplaceUserPermissions(_replace_deps(permissions, audit)).execute(
        target_user_id=target,
        desired=PermissionSet(granted=frozenset({_VER_INSUMOS})),
        actor_user_id=uuid.uuid4(),
    )

    assert permissions.replaced == []
    assert audit.diffs == []


async def test_con_diff_reemplaza_y_audita_altas_y_bajas() -> None:
    permissions = FakePermissionRepository()
    audit = FakePermissionAuditRepository()
    target, actor = uuid.uuid4(), uuid.uuid4()
    permissions.by_user[target] = PermissionSet(granted=frozenset({_VER_INSUMOS}))
    desired = PermissionSet(granted=frozenset({_VER_TURNOS}))

    await ReplaceUserPermissions(_replace_deps(permissions, audit)).execute(
        target_user_id=target, desired=desired, actor_user_id=actor
    )

    assert permissions.replaced == [(target, desired, actor)]
    assert len(audit.diffs) == 1
    assert audit.diffs[0].added == frozenset({_VER_TURNOS})
    assert audit.diffs[0].removed == frozenset({_VER_INSUMOS})


def _entry(key: str, *, enabled: bool = True) -> ModuleCatalogEntry:
    return ModuleCatalogEntry(
        key=ModuleKey(key),
        label=key.title(),
        route=f"/{key}",
        icon="icon",
        sort_order=1,
        is_enabled=enabled,
        actions=frozenset({ActionKey("view")}),
    )


class FakeModuleCatalogRepository:
    def __init__(self, entries: list[ModuleCatalogEntry]) -> None:
        self.entries = entries
        self.actions = [ActionCatalogEntry(key=ActionKey("view"), label="Ver")]

    async def list_all(self) -> list[ModuleCatalogEntry]:
        return self.entries

    async def list_actions(self) -> list[ActionCatalogEntry]:
        return self.actions


async def test_superadmin_ve_todo_lo_habilitado_sin_grants() -> None:
    catalog = FakeModuleCatalogRepository(
        [_entry("insumos"), _entry("turnos"), _entry("stc", enabled=False)]
    )
    deps = ListVisibleModulesDependencies(catalog=catalog, permissions=FakePermissionRepository())

    visibles = await ListVisibleModules(deps).execute(user_id=uuid.uuid4(), is_superadmin=True)

    assert [e.key.value for e in visibles] == ["insumos", "turnos"]


async def test_usuario_comun_solo_ve_modulos_con_algun_grant() -> None:
    catalog = FakeModuleCatalogRepository([_entry("insumos"), _entry("turnos")])
    permissions = FakePermissionRepository()
    user_id = uuid.uuid4()
    permissions.by_user[user_id] = PermissionSet(granted=frozenset({_VER_TURNOS}))
    deps = ListVisibleModulesDependencies(catalog=catalog, permissions=permissions)

    visibles = await ListVisibleModules(deps).execute(user_id=user_id, is_superadmin=False)

    assert [e.key.value for e in visibles] == ["turnos"]


async def test_los_catalogos_y_get_user_permissions_delegan_al_repo() -> None:
    catalog = FakeModuleCatalogRepository([_entry("insumos")])
    permissions = FakePermissionRepository()
    user_id = uuid.uuid4()
    granted = PermissionSet(granted=frozenset({MANAGE_ADMIN}))
    permissions.by_user[user_id] = granted

    modules = await ListModuleCatalog(ListModuleCatalogDependencies(catalog=catalog)).execute()
    actions = await ListActionCatalog(ListActionCatalogDependencies(catalog=catalog)).execute()
    permisos = await GetUserPermissions(
        GetUserPermissionsDependencies(permissions=permissions)
    ).execute(user_id)

    assert modules == catalog.entries
    assert actions == catalog.actions
    assert permisos == granted
