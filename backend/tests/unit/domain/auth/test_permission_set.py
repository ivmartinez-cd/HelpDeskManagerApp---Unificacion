from src.modules.auth.domain.value_objects.action_key import ActionKey
from src.modules.auth.domain.value_objects.module_key import ModuleKey
from src.modules.auth.domain.value_objects.permission import Permission
from src.modules.auth.domain.value_objects.permission_set import PermissionSet

_INSUMOS_VIEW = Permission(ModuleKey("insumos"), ActionKey("view"))


def test_allows_a_granted_permission() -> None:
    permissions = PermissionSet(frozenset({_INSUMOS_VIEW}))

    assert permissions.allows(_INSUMOS_VIEW) is True


def test_denies_a_permission_that_was_never_granted() -> None:
    permissions = PermissionSet(frozenset({_INSUMOS_VIEW}))
    ungranted = Permission(ModuleKey("insumos"), ActionKey("delete"))

    assert permissions.allows(ungranted) is False


def test_denies_a_permission_for_an_unknown_module_or_action() -> None:
    """No existe tal cosa como un módulo/acción "inválido" para PermissionSet:
    cualquier par no concedido explícitamente es simplemente False."""
    permissions = PermissionSet(frozenset())
    unknown_module = Permission(ModuleKey("nunca-existio"), ActionKey("view"))
    unknown_action = Permission(ModuleKey("insumos"), ActionKey("nunca-existio"))

    assert permissions.allows(unknown_module) is False
    assert permissions.allows(unknown_action) is False


def test_modules_aggregates_the_distinct_modules_granted() -> None:
    permissions = PermissionSet(
        frozenset({_INSUMOS_VIEW, Permission(ModuleKey("insumos"), ActionKey("export"))})
    )

    assert permissions.modules() == frozenset({ModuleKey("insumos")})
