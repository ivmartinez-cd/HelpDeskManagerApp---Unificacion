"""Importa la caché de tipificaciones del legacy `reporte-incidentes` a HDM.

Uso (dentro del contenedor del backend; `backend/var/` está en .gitignore porque el
archivo trae textos reales de incidentes de clientes):

    cp ~/proyectos/canal/reporte-incidentes/src/lib/data/classification-cache.json backend/var/
    docker exec helpdesk-manager-backend uv run python \
        -m scripts.importar_tipificaciones_reporte_incidentes var/classification-cache.json

El JSON es `{ "<descripcion>|<causa>|<solucion>": {categoria, subcategoria, confianza?} }`.
La clave se guarda tal cual (misma función `clave_caso` que usa el módulo), así que
los incidentes ya tipificados en el legacy salen tipificados en HDM sin volver a
pagar la IA. Idempotente: re-correrlo reemplaza por clave. `confianza` ausente vale
"alta" (mismo default que el legacy al leer). Origen "legacy".
"""

import asyncio
import json
import sys
from pathlib import Path

from src.modules.reporte_incidentes.domain.entities.categoria import TipificacionGuardada
from src.modules.reporte_incidentes.infrastructure.repositories.sqlalchemy_tipificaciones import (
    SqlAlchemyTipificacionCacheRepository,
)
from src.shared.infrastructure.database.session import get_sessionmaker

_TANDA = 500


def _leer(ruta: Path) -> dict[str, TipificacionGuardada]:
    crudo: dict[str, dict[str, str]] = json.loads(ruta.read_text(encoding="utf-8"))
    return {
        clave: TipificacionGuardada(
            v["categoria"], v.get("subcategoria", ""), (v.get("confianza") or "alta").lower()
        )
        for clave, v in crudo.items()
    }


async def _importar(tipificaciones: dict[str, TipificacionGuardada]) -> None:
    items = list(tipificaciones.items())
    async with get_sessionmaker()() as session, session.begin():
        repo = SqlAlchemyTipificacionCacheRepository(session, origen="legacy")
        for inicio in range(0, len(items), _TANDA):
            await repo.guardar(dict(items[inicio : inicio + _TANDA]))


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Uso: python -m scripts.importar_tipificaciones_reporte_incidentes <json>")
    tipificaciones = _leer(Path(sys.argv[1]))
    asyncio.run(_importar(tipificaciones))
    alta = sum(t.confianza == "alta" for t in tipificaciones.values())
    print(f"Importadas {len(tipificaciones)} tipificaciones ({alta} con confianza alta).")


if __name__ == "__main__":
    main()
