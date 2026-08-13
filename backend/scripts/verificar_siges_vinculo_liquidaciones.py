"""Verificación end-to-end del dataset 1 del ADR-014 contra la DB real y Siges real.

Ejercita los use cases reales (no HTTP, para no depender de una sesión de login):
1. Rutas registradas en la app (openapi).
2. Propuestas de vínculo contra Siges real.
3. --aplicar: confirma las propuestas (vincular), sync dry-run, sync real y
   re-corrida para verificar idempotencia. Sin --aplicar no escribe nada.

Uso (dentro del contenedor backend):
    uv run python scripts/verificar_siges_vinculo_liquidaciones.py [--aplicar]
"""

import asyncio
import sys

from src.modules.liquidaciones.application.use_cases.siges_config import (
    ProponerVinculosSiges,
    SigesConfigPorts,
    SyncConfigDesdeSiges,
    VincularPrestadorSiges,
    VincularSpstSiges,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_spst_repository import (
    SqlAlchemySpstRepository,
)
from src.modules.liquidaciones.infrastructure.siges.pyodbc_siges_catalogo_gateway import (
    PyodbcSigesCatalogoGateway,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_sessionmaker
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string


def _verificar_rutas() -> None:
    from src.shared.presentation.app import create_app

    paths = create_app().openapi()["paths"]
    esperadas = [
        "/api/liquidaciones/siges/propuestas",
        "/api/liquidaciones/siges/sync",
        "/api/liquidaciones/prestadores/{prestador_id}/siges-vinculo",
        "/api/liquidaciones/spsts/{spst_id}/siges-vinculo",
    ]
    for ruta in esperadas:
        assert ruta in paths, f"Falta la ruta {ruta}"
    print(f"Rutas OK ({len(esperadas)} registradas)")


def _imprimir_sync(titulo: str, resultado: object) -> None:
    print(f"\n=== {titulo} ===")
    print(resultado)


async def main() -> None:
    aplicar = "--aplicar" in sys.argv
    _verificar_rutas()

    settings = get_settings()
    gateway = PyodbcSigesCatalogoGateway(
        build_mercurio_connection_string(settings), settings.sla_mercurio_timeout_seconds
    )
    async with get_sessionmaker()() as session:
        ports = SigesConfigPorts(
            prestadores=SqlAlchemyPrestadorRepository(session),
            spsts=SqlAlchemySpstRepository(session),
            siges=gateway,
        )
        propuestas = await ProponerVinculosSiges(ports).execute()
        print(f"\nPropuestas: {len(propuestas.propuestas)} | Disponibles sin vincular: "
              f"{len(propuestas.disponibles)}")
        for p in propuestas.propuestas:
            print(f"  [{p.entidad}] {p.local_nombre!r} ↔ #{p.siges_empresa_id} "
                  f"{p.siges_den_comercial!r}")

        if not aplicar:
            print("\n(sin --aplicar: no se escribió nada)")
            return

        for p in propuestas.propuestas:
            if p.entidad == "prestador":
                await VincularPrestadorSiges(ports).execute(
                    p.local_id, siges_empresa_id=p.siges_empresa_id
                )
            else:
                await VincularSpstSiges(ports).execute(
                    p.local_id, siges_empresa_id=p.siges_empresa_id
                )
        print(f"\nVinculados: {len(propuestas.propuestas)}")

        dry = await SyncConfigDesdeSiges(ports).execute(dry_run=True)
        _imprimir_sync("Sync dry-run", dry)
        real = await SyncConfigDesdeSiges(ports).execute(dry_run=False)
        _imprimir_sync("Sync real", real)
        de_nuevo = await SyncConfigDesdeSiges(ports).execute(dry_run=False)
        _imprimir_sync("Sync re-corrida (idempotencia)", de_nuevo)
        assert de_nuevo.cambios == [], "La re-corrida no fue idempotente"

        await session.commit()
        print("\nCommit OK — idempotencia verificada.")


if __name__ == "__main__":
    asyncio.run(main())
