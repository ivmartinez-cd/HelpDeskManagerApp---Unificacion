"""Endpoints para actuar sobre Insumos > Despachados: "Actualizar ahora", registrar una
acción sobre una guía, cerrar su alerta y preparar un reclamo en OCA. Exigen
`insumos.update`.

"Actualizar ahora" no espera a OCA: lanza la corrida en segundo plano y responde 202; la
pantalla sigue su avance con `GET /despachados/actualizacion`.
"""

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.application.use_cases.despachados.acciones_despacho import (
    DatosAccion,
    UsuarioActuante,
)
from src.modules.insumos.domain.errores_despachados import SincronizacionDespachosEnCursoError
from src.modules.insumos.domain.well_known_permissions import UPDATE
from src.modules.insumos.presentation.dependencies import (
    build_cerrar_alerta_despacho,
    build_consultar_actualizacion,
    build_registrar_accion_despacho,
)
from src.modules.insumos.presentation.dependencies.despachados import (
    build_preparar_reclamo_oca,
    get_despachados_lock,
)
from src.modules.insumos.presentation.despachados_jobs import lanzar_actualizacion_manual
from src.modules.insumos.presentation.despachados_router import PATRON_GUIA
from src.modules.insumos.presentation.schemas.despachados_detalle_schemas import EnvioOut
from src.modules.insumos.presentation.schemas.despachados_reclamo_schemas import ReclamoOcaOut
from src.modules.insumos.presentation.schemas.despachados_schemas import (
    AccionIn,
    AccionOut,
    ActualizacionLanzadaOut,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/insumos", tags=["insumos"])

_require_update = Depends(require_permission(UPDATE))


def _usuario(identity: Identity) -> UsuarioActuante:
    """Quien actúa: su id y su nombre visible (queda en la acción y en el cierre)."""
    return UsuarioActuante(id=identity.user.id, nombre=identity.user.full_name)


async def _corrida_en_curso(db: AsyncSession) -> bool:
    """La base dice que la última corrida no terminó y el candado lo confirma. Si el
    candado está libre, esa corrida quedó colgada por un reinicio: no bloquea el botón (la
    próxima corrida la cierra como interrumpida)."""
    if not (await build_consultar_actualizacion(db).execute()).en_curso:
        return False
    async with get_despachados_lock().hold() as obtenido:
        return not obtenido


@router.post(
    "/despachados/actualizar",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ActualizacionLanzadaOut,
)
async def actualizar_despachados(
    identity: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ActualizacionLanzadaOut:
    """Lanza "Actualizar ahora" en segundo plano (sin mirar la ventana del job). 409
    `SINCRONIZACION_DESPACHOS_EN_CURSO` si ya hay una corrida corriendo."""
    if await _corrida_en_curso(db):
        raise SincronizacionDespachosEnCursoError()
    lanzar_actualizacion_manual(identity.user.full_name)
    return ActualizacionLanzadaOut()


@router.post(
    "/despachados/{guia}/acciones",
    status_code=status.HTTP_201_CREATED,
    response_model=AccionOut,
)
async def registrar_accion(
    body: AccionIn,
    guia: str = Path(pattern=PATRON_GUIA),
    identity: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> AccionOut:
    """Registra una acción del operador; con `cerrarAlerta` además da la alerta por
    atendida (409 `ALERTA_DESPACHO_NO_ABIERTA` si no estaba abierta)."""
    datos = DatosAccion(
        tipo=body.tipo,
        detalle=body.detalle,
        resultado=body.resultado,
        cerrar_alerta=body.cerrar_alerta,
    )
    accion = await build_registrar_accion_despacho(db).execute(guia, datos, _usuario(identity))
    return AccionOut.from_accion(accion)


@router.post("/despachados/{guia}/cerrar-alerta", response_model=EnvioOut)
async def cerrar_alerta(
    guia: str = Path(pattern=PATRON_GUIA),
    identity: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> EnvioOut:
    """Da la alerta por atendida y devuelve el envío actualizado (200, para refrescar la
    fila sin otra lectura). 409 si no está abierta o si todavía no hay ninguna acción."""
    envio = await build_cerrar_alerta_despacho(db).execute(guia, _usuario(identity))
    return EnvioOut.from_envio(envio)


@router.get("/despachados/{guia}/reclamo-oca", response_model=ReclamoOcaOut)
async def preparar_reclamo_oca(
    guia: str = Path(pattern=PATRON_GUIA),
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ReclamoOcaOut:
    """Datos para precargar el formulario público de reclamos de OCA (contacto de la cuenta
    según el prefijo de la guía, o null; comentario sugerido). No escribe ni llama a OCA:
    exige `insumos.update` porque es el primer paso de una acción. 404 si la guía no se
    sigue."""
    reclamo = await build_preparar_reclamo_oca(db).execute(guia)
    return ReclamoOcaOut.from_reclamo(reclamo)
