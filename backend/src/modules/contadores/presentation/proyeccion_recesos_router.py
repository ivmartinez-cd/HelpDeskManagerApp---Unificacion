"""Recesos de clientes de la herramienta Proyección (`Recesos.razor` del
Estimador v1.7): listar, agregar, editar y eliminar. Incluido en
`proyeccion_router.py` (mismo prefix). Sin grupo económico real (o con el de
ejemplo) opera sobre el store en memoria del modo ejemplo."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.use_cases.gestionar_recesos_proyeccion import (
    CrearRecesoRequest,
    GestionarRecesosProyeccionUseCase,
)
from src.modules.contadores.domain.ports.recesos_port import RecesosPort
from src.modules.contadores.domain.well_known_permissions import MANAGE, VIEW
from src.modules.contadores.infrastructure.ejemplo.datos_ejemplo_proyeccion import (
    ID_GRUPO_ECONOMICO_EJEMPLO,
)
from src.modules.contadores.infrastructure.ejemplo.recesos_store import get_recesos_ejemplo_store
from src.modules.contadores.infrastructure.repositories.sqlalchemy_recesos_repository import (
    SqlAlchemyRecesosRepository,
)
from src.modules.contadores.presentation.schemas.proyeccion_schemas import RecesoSchema
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()

_require_view = Depends(require_permission(VIEW))
_require_manage = Depends(require_permission(MANAGE))
_db = Depends(get_db, scope="function")
_TAMANIO_PAGINA_MINIMO = 50


@router.get("/recesos", response_model=Page[RecesoSchema])
async def list_recesos(
    id_grupo_economico: int | None = None,
    _: Identity = _require_view,
    db: AsyncSession = _db,
) -> Page[RecesoSchema]:
    """Sin `id_grupo_economico` (o si coincide con el de ejemplo), lista los
    recesos de ejemplo — con un grupo económico real, los de ese grupo en
    Postgres. La lista es chica y no se pagina en la UI: `size` nunca corta."""
    store = _recesos_store_de(id_grupo_economico, db)
    recesos = await store.listar(id_grupo_economico or ID_GRUPO_ECONOMICO_EJEMPLO)
    items = [RecesoSchema.from_dto(r) for r in recesos]
    return Page.of(items, page=1, size=max(len(items), _TAMANIO_PAGINA_MINIMO))


@router.post("/recesos", response_model=RecesoSchema, status_code=201)
async def crear_receso(
    request: CrearRecesoRequest,
    _: Identity = _require_manage,
    db: AsyncSession = _db,
) -> RecesoSchema:
    store = _recesos_store_de(request.id_grupo_economico, db)
    use_case = GestionarRecesosProyeccionUseCase(store)
    return RecesoSchema.from_dto(await use_case.crear(request))


@router.put("/recesos/{id_receso}", response_model=RecesoSchema)
async def actualizar_receso(
    id_receso: int,
    request: CrearRecesoRequest,
    _: Identity = _require_manage,
    db: AsyncSession = _db,
) -> RecesoSchema:
    """El "Editar" de `Recesos.razor` (`ActualizarAsync`): pisa todos los campos."""
    store = _recesos_store_de(request.id_grupo_economico, db)
    actualizado = await GestionarRecesosProyeccionUseCase(store).actualizar(id_receso, request)
    if actualizado is None:
        raise HTTPException(status_code=404, detail="Receso no encontrado")
    return RecesoSchema.from_dto(actualizado)


@router.delete("/recesos/{id_receso}", status_code=204)
async def eliminar_receso(
    id_receso: int,
    id_grupo_economico: int | None = None,
    _: Identity = _require_manage,
    db: AsyncSession = _db,
) -> None:
    store = _recesos_store_de(id_grupo_economico, db)
    await GestionarRecesosProyeccionUseCase(store).eliminar(id_receso)


def _recesos_store_de(id_grupo_economico: int | None, db: AsyncSession) -> RecesosPort:
    if id_grupo_economico is None or id_grupo_economico == ID_GRUPO_ECONOMICO_EJEMPLO:
        return get_recesos_ejemplo_store()
    return SqlAlchemyRecesosRepository(db)
