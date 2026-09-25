from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.reporte_incidentes.domain.entities.categoria import TipificacionGuardada
from src.modules.reporte_incidentes.domain.services.tipificacion import hash_clave
from src.modules.reporte_incidentes.infrastructure.models.taxonomia_models import (
    ReporteIncidentesTipificacionModel as Modelo,
)

# Postgres acota los parámetros por sentencia: se consulta de a tandas.
_TANDA = 1000


class SqlAlchemyTipificacionCacheRepository:
    def __init__(self, session: AsyncSession, origen: str = "ia") -> None:
        self._session = session
        self._origen = origen

    async def obtener(self, claves: set[str]) -> dict[str, TipificacionGuardada]:
        por_hash = {hash_clave(c): c for c in claves}
        hashes = list(por_hash)
        encontradas: dict[str, TipificacionGuardada] = {}
        for inicio in range(0, len(hashes), _TANDA):
            stmt = select(Modelo).where(Modelo.clave_hash.in_(hashes[inicio : inicio + _TANDA]))
            for fila in (await self._session.execute(stmt)).scalars():
                encontradas[por_hash[fila.clave_hash]] = TipificacionGuardada(
                    fila.categoria, fila.subcategoria, fila.confianza
                )
        return encontradas

    async def guardar(self, tipificaciones: dict[str, TipificacionGuardada]) -> None:
        if not tipificaciones:
            return
        filas = [self._fila(clave, t) for clave, t in tipificaciones.items()]
        stmt = pg_insert(Modelo).values(filas)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Modelo.clave_hash],
            set_={
                "categoria": stmt.excluded.categoria,
                "subcategoria": stmt.excluded.subcategoria,
                "confianza": stmt.excluded.confianza,
                "origen": stmt.excluded.origen,
                "updated_at": func.now(),
            },
        )
        await self._session.execute(stmt)

    def _fila(self, clave: str, t: TipificacionGuardada) -> dict[str, str]:
        return {
            "clave_hash": hash_clave(clave), "clave": clave, "categoria": t.categoria,
            "subcategoria": t.subcategoria, "confianza": t.confianza, "origen": self._origen,
        }
