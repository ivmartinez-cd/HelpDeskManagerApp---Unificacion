from collections.abc import Awaitable, Callable

from fastapi import Depends

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.domain.errors import ForbiddenError
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.shared.domain.value_objects.feature_key import FeatureKey


def require_feature(feature: FeatureKey) -> Callable[..., Awaitable[Identity]]:
    """Fail-closed: sin la función concedida -> 403 (ADR-032). El superadmin la
    tiene implícita, igual que con `require_permission`. Se usa en los
    endpoints que respaldan una pantalla/card concedible por usuario (anexos
    sin facturar, clientes nuevos, reportes de personal…); las mutaciones
    siguen exigiendo además la acción que corresponda."""

    async def _check(identity: Identity = Depends(get_current_identity)) -> Identity:
        if identity.user.is_superadmin or feature.value in identity.features:
            return identity
        raise ForbiddenError()

    return _check


def tiene_feature(identity: Identity, feature: FeatureKey) -> bool:
    """Variante sin dependencia, para ramificar dentro de un endpoint que ya
    exige otra cosa (p. ej. "ver todos" vs "solo lo mío")."""
    return identity.user.is_superadmin or feature.value in identity.features
