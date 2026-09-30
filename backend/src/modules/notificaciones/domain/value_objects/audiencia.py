"""A quién le llega una notificación: a todos los que tengan una función
concedida (ADR-032) o un permiso de módulo. Se guarda como texto
(`funcion:<clave>` / `permiso:<módulo>.<acción>`) para que listar las de un
usuario sea un `IN` sobre sus propias audiencias, sin joins contra auth."""

from src.shared.domain.value_objects.feature_key import FeatureKey
from src.shared.domain.value_objects.permission import Permission


def audiencia_funcion(funcion: FeatureKey) -> str:
    return f"funcion:{funcion.value}"


def audiencia_permiso(permiso: Permission) -> str:
    return f"permiso:{permiso.module.value}.{permiso.action.value}"


def audiencias_de(
    funciones: frozenset[str], permisos: frozenset[tuple[str, str]]
) -> frozenset[str]:
    """Todas las audiencias a las que pertenece un usuario, a partir de sus
    funciones y sus permisos `(módulo, acción)`."""
    return frozenset(f"funcion:{f}" for f in funciones) | frozenset(
        f"permiso:{m}.{a}" for m, a in permisos
    )
