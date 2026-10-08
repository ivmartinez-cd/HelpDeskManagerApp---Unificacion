import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import column, func, select, table, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.reportes_app.infrastructure.models.reporte_app_model import ReporteAppModel as R

# Solo el nombre de quien reportó: tabla liviana en vez de importar el modelo de auth.
_usuarios = table("app_user", column("id"), column("full_name"))


@dataclass(frozen=True, slots=True)
class ReporteVista:
    id: uuid.UUID
    tipo: str
    estado: str
    ruta: str
    detalle: str
    tiene_foto: bool
    nota: str | None
    respuesta: str | None
    rama: str | None
    usuario: str | None
    creado_en: datetime
    actualizado_en: datetime | None


class SqlAlchemyReporteAppRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(
        self,
        *,
        tipo: str,
        detalle: str,
        ruta: str,
        foto: str | None,
        usuario_id: uuid.UUID,
    ) -> uuid.UUID:
        reporte = R(tipo=tipo, detalle=detalle, ruta=ruta, foto=foto, usuario_id=usuario_id)
        self._session.add(reporte)
        await self._session.flush()
        return reporte.id

    async def listar(
        self, estado: str | None, *, offset: int, limit: int
    ) -> tuple[list[ReporteVista], int]:
        """Más recientes primero. Devuelve (página, total que cumple el filtro)."""
        filtro = R.estado == estado if estado else R.id.is_not(None)
        total = await self._session.scalar(select(func.count()).select_from(R).where(filtro))
        consulta = (
            select(R, _usuarios.c.full_name)
            .outerjoin(_usuarios, _usuarios.c.id == R.usuario_id)
            .where(filtro)
            .order_by(R.creado_en.desc())
            .offset(offset)
            .limit(limit)
        )
        filas = await self._session.execute(consulta)
        return [_vista(r, nombre) for r, nombre in filas], total or 0

    async def nombre_foto(self, reporte_id: uuid.UUID) -> str | None:
        return await self._session.scalar(select(R.foto).where(R.id == reporte_id))

    async def decidir(self, reporte_id: uuid.UUID, estado: str, respuesta: str | None) -> bool:
        """Guarda la decisión del superadmin. False si el reporte no existe."""
        resultado = await self._session.execute(
            update(R)
            .where(R.id == reporte_id)
            .values(estado=estado, respuesta=respuesta, actualizado_en=func.now())
        )
        return bool(getattr(resultado, "rowcount", 0))

    async def pedir_integracion(self, reporte_id: uuid.UUID) -> bool:
        """Solo un `resuelto` con rama. False si no aplica (o no existe)."""
        resultado = await self._session.execute(
            update(R)
            .where(R.id == reporte_id, R.estado == "resuelto", R.rama.is_not(None))
            .values(estado="integrar", actualizado_en=func.now())
        )
        return bool(getattr(resultado, "rowcount", 0))


def _vista(r: R, usuario: str | None) -> ReporteVista:
    return ReporteVista(
        id=r.id,
        tipo=r.tipo,
        estado=r.estado,
        ruta=r.ruta,
        detalle=r.detalle,
        tiene_foto=r.foto is not None,
        nota=r.nota,
        respuesta=r.respuesta,
        rama=r.rama,
        usuario=usuario,
        creado_en=r.creado_en,
        actualizado_en=r.actualizado_en,
    )
