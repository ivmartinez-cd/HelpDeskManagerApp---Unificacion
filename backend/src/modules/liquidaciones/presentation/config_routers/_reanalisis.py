"""Reanálisis automático tras un cambio de configuración (tarifarios, Tabla KM,
vínculo SPST): el motor de reglas vuelve a correr sobre las liquidaciones
abiertas del prestador tocado. Sin esto, la corrección quedaba invisible hasta
que alguien apretara "Reanalizar" en el detalle de cada liquidación.

Best-effort a propósito: la escritura de configuración ya está hecha y es lo
que el usuario pidió; si el reanálisis falla se loguea con contexto (§6) y el
request responde igual. Como `get_db(scope="function")` commitea al final
(ADR-030), un error de DB dentro del reanálisis puede voltear también la
escritura — se acepta como caso raro antes que dejar alertas obsoletas en
silencio."""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.presentation.dependencies import (
    build_reanalizar_liquidaciones_abiertas,
)

logger = logging.getLogger(__name__)


async def reanalizar_abiertas(db: AsyncSession, prestador_id: UUID | None) -> None:
    try:
        await build_reanalizar_liquidaciones_abiertas(db).execute(prestador_id)
    except Exception as exc:
        logger.error(
            "reanálisis automático tras cambio de configuración falló",
            extra={"prestador_id": str(prestador_id)},
            exc_info=exc,
        )
