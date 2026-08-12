"""Placeholder de FastAPI para el puerto `OperadorColorLookup` (ver
`auth.domain.repositories.operador_color_lookup`). La implementación real
cruza a contadores — importarla acá violaría `auth-independent-from-
contadores` (import-linter es transitivo: hasta un adaptador en `shared` que
internamente importe contadores rompe el contrato si algo bajo `src.modules.
auth` lo importa). En vez de eso, `src/shared/presentation/app.py` (la raíz
de composición, sin restricciones de import-linter) override esta función
con la implementación concreta vía `app.dependency_overrides`. Ver
`docs/adr/009-inyeccion-cruzada-auth-contadores-color-operador.md`."""

from src.modules.auth.domain.repositories.operador_color_lookup import OperadorColorLookup


async def get_operador_color_lookup() -> OperadorColorLookup:
    raise NotImplementedError(
        "get_operador_color_lookup no fue overrideado — falta el wiring en "
        "src/shared/presentation/app.py"
    )
