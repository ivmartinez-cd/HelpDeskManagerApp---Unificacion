"""Verificación end-to-end del dataset 2 del ADR-014 (sync de tarifarios) contra
la DB real y Siges real, vía los use cases reales.

Sin flags: estado de zonas + sync dry-run (no escribe nada).
--mapear: confirma las propuestas automáticas de zona (y el mapeo manual de
  General Roca de INFOMAC, inequívoco a ojo pero fuera del alcance del matching).
--aplicar: sync real + re-corrida para verificar idempotencia.

Uso (dentro del contenedor backend):
    uv run python scripts/verificar_siges_tarifarios_liquidaciones.py [--mapear] [--aplicar]
"""

import asyncio
import sys
from collections import Counter

from src.modules.liquidaciones.application.dtos.siges_tarifarios import SyncTarifariosResultado
from src.modules.liquidaciones.application.use_cases.siges_tarifarios import (
    EstadoZonasSiges,
    MapearZonaSiges,
    SigesTarifariosPorts,
    SyncTarifariosDesdeSiges,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_spst_repository import (
    SqlAlchemySpstRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tarifario_repository import (  # noqa: E501
    SqlAlchemyTarifarioRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tarifario_zona_map_repository import (  # noqa: E501
    SqlAlchemyTarifarioZonaMapRepository,
)
from src.modules.liquidaciones.infrastructure.siges.pyodbc_siges_catalogo_gateway import (
    PyodbcSigesCatalogoGateway,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_sessionmaker
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

# Mapeos manuales confirmados a ojo. Valor None = zona genérica (sin zona).
# Los códigos TMT* son la tarifa genérica de cada PST (hipótesis confirmada por
# conteos exactos: MENDOZA 192=192, SALTA 192=192, MACARONE 198=198, CATAMARCA
# 138=138 con zona local NULL) — se mapean a genérica por regla, no por tabla.
_MAPEOS_MANUALES: dict[tuple[str, str], str | None] = {
    ("INFOMAC", "General Roca / Rio Negro / Neuquen / Cipoletti"): "Gral. Roca / Neuquén",
}
# GSJ - * de SAN JUAN quedan sin mapear a propósito: son excepciones de zona sin
# zona local equivalente (decisión de la TL, no del script).
_SIN_MAPEAR_A_PROPOSITO = {"GSJ - Escuelas Valle Fertil", "GSJ - GI Centro Civico"}


def _resumir_sync(titulo: str, r: SyncTarifariosResultado) -> None:
    print(f"\n=== {titulo} ===")
    print(f"creados={r.creados} sin_cambios={r.sin_cambios} conflictos={len(r.conflictos)} "
          f"zonas_sin_mapear={len(r.zonas_sin_mapear)} sin_vinculo={len(r.prestadores_sin_vinculo)}")
    creados_por_pst = Counter()
    for g in r.grupos_creados:
        creados_por_pst[g.prestador] += g.cantidad
    for prestador, cantidad in sorted(creados_por_pst.items()):
        print(f"  a crear {prestador}: {cantidad}")
    for z in r.zonas_sin_mapear:
        print(f"  SIN MAPEAR {z.prestador}: {z.descripcion_siges!r} ({z.filas} filas)")
    for c in r.conflictos[:20]:
        print(f"  CONFLICTO {c.prestador} {c.tipo_servicio} zona={c.zona!r} "
              f"desde={c.vigencia_desde} {c.campo}: local={c.valor_local} siges={c.valor_siges}")
    if len(r.conflictos) > 20:
        print(f"  ... y {len(r.conflictos) - 20} conflicto(s) más")


async def main() -> None:
    mapear = "--mapear" in sys.argv
    aplicar = "--aplicar" in sys.argv
    settings = get_settings()
    gateway = PyodbcSigesCatalogoGateway(
        build_mercurio_connection_string(settings), settings.sla_mercurio_timeout_seconds
    )
    async with get_sessionmaker()() as session:
        ports = SigesTarifariosPorts(
            prestadores=SqlAlchemyPrestadorRepository(session),
            tarifarios=SqlAlchemyTarifarioRepository(session),
            spsts=SqlAlchemySpstRepository(session),
            zona_maps=SqlAlchemyTarifarioZonaMapRepository(session),
            siges=gateway,
        )
        zonas = await EstadoZonasSiges(ports).execute()
        print(f"=== Zonas detectadas: {len(zonas.zonas)} ===")
        for z in zonas.zonas:
            estado = f"mapeada -> {z.zona_local!r}" if z.zona_local else (
                f"propuesta -> {z.propuesta!r}" if z.propuesta else "SIN MAPEO NI PROPUESTA"
            )
            print(f"  {z.prestador}: {z.descripcion_siges!r} [{estado}]")

        if mapear:
            mapeadas = 0
            for z in zonas.zonas:
                if z.mapeada or z.descripcion_siges in _SIN_MAPEAR_A_PROPOSITO:
                    continue
                clave = (z.prestador, z.descripcion_siges)
                if z.descripcion_siges.startswith("TMT"):
                    destino: str | None = None  # código de tarifa = genérica
                elif z.propuesta:
                    destino = z.propuesta
                elif clave in _MAPEOS_MANUALES:
                    destino = _MAPEOS_MANUALES[clave]
                else:
                    continue
                await MapearZonaSiges(ports).execute(
                    z.prestador_id, descripcion_siges=z.descripcion_siges, zona_local=destino
                )
                mapeadas += 1
            print(f"\nMapeos confirmados: {mapeadas}")

        dry = await SyncTarifariosDesdeSiges(ports).execute(dry_run=True)
        _resumir_sync("Sync tarifarios dry-run", dry)

        if not aplicar:
            if mapear:
                await session.commit()
                print("\nCommit de mapeos OK (sin sync real: falta --aplicar).")
            else:
                print("\n(sin --mapear/--aplicar: no se escribió nada)")
            return

        real = await SyncTarifariosDesdeSiges(ports).execute(dry_run=False)
        _resumir_sync("Sync tarifarios real", real)
        de_nuevo = await SyncTarifariosDesdeSiges(ports).execute(dry_run=False)
        _resumir_sync("Re-corrida (idempotencia)", de_nuevo)
        assert de_nuevo.creados == 0, "La re-corrida no fue idempotente"
        await session.commit()
        print("\nCommit OK — idempotencia verificada.")


if __name__ == "__main__":
    asyncio.run(main())
