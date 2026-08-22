"""Auditoría (registrador + lectura paginada), directorio de usuarios y
destinatarios de nueva solicitud, contra Postgres real."""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.permission_models import (
    Action,
    Module,
    ModuleAction,
    PermissionGrant,
    UserModuleScope,
)
from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.vacaciones.domain.repositories.auditoria import FiltrosAuditoria
from src.modules.vacaciones.infrastructure.models.audit_log_model import (
    VacacionesAuditLogModel,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_auditoria import (
    SqlAlchemyAuditoriaRepository,
    SqlAlchemyRegistradorAuditoria,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_destinatarios import (
    SqlAlchemyDestinatariosNuevaSolicitud,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_user_directory import (
    SqlAlchemyUserDirectory,
)


async def _user(db_session: AsyncSession, nombre: str, *, activo: bool = True) -> AppUser:
    user = AppUser(
        id=uuid.uuid4(),
        email=f"{nombre.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}@canal.com",
        password_hash="x",
        full_name=nombre,
        is_active=activo,
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def test_registrador_escribe_y_list_pagina_filtra_por_entidad_accion_y_fechas(
    db_session: AsyncSession,
) -> None:
    actor = await _user(db_session, "Actor Auditoria")
    registrador = SqlAlchemyRegistradorAuditoria(db_session, actor.id)
    entidad = f"Ent-{uuid.uuid4().hex[:8]}"
    await registrador.registrar("CREATE", entidad, "1", {"campo": "valor"})
    await registrador.registrar("UPDATE", entidad, "1", {})
    await registrador.registrar("DELETE", entidad, None, {"motivo": "x"})
    # Dentro de una misma transacción `now()` es constante: se separan los
    # created_at a mano para que el orden desc sea verificable.
    for accion, minutos in (("CREATE", 3), ("UPDATE", 2), ("DELETE", 1)):
        await db_session.execute(
            update(VacacionesAuditLogModel)
            .where(
                VacacionesAuditLogModel.entidad == entidad,
                VacacionesAuditLogModel.accion == accion,
            )
            .values(created_at=datetime.now(UTC) - timedelta(minutes=minutos))
        )

    repo = SqlAlchemyAuditoriaRepository(db_session)
    todos, total = await repo.list_pagina(FiltrosAuditoria(entidad=entidad), offset=0, limit=10)
    assert total == 3
    assert [r.accion for r in todos] == ["DELETE", "UPDATE", "CREATE"]
    assert todos[-1].metadata == {"campo": "valor"}
    assert todos[1].metadata == {}  # metadata vacía se guarda como NULL y vuelve como {}
    assert todos[0].user_id == actor.id

    pagina, total = await repo.list_pagina(
        FiltrosAuditoria(entidad=entidad), offset=1, limit=1
    )
    assert total == 3
    assert [r.accion for r in pagina] == ["UPDATE"]

    solo_create, _ = await repo.list_pagina(
        FiltrosAuditoria(entidad=entidad, accion="CREATE"), offset=0, limit=10
    )
    assert [r.entidad_id for r in solo_create] == ["1"]

    hoy = date.today()
    en_rango, _ = await repo.list_pagina(
        FiltrosAuditoria(entidad=entidad, desde=hoy - timedelta(days=1), hasta=hoy),
        offset=0,
        limit=10,
    )
    assert len(en_rango) == 3
    fuera, total_fuera = await repo.list_pagina(
        FiltrosAuditoria(entidad=entidad, desde=hoy + timedelta(days=2)), offset=0, limit=10
    )
    assert (fuera, total_fuera) == ([], 0)


async def test_list_pagina_search_matchea_accion_entidad_o_email(
    db_session: AsyncSession,
) -> None:
    actor = await _user(db_session, "Buscable Persona")
    entidad = f"Ent-{uuid.uuid4().hex[:8]}"
    await SqlAlchemyRegistradorAuditoria(db_session, actor.id).registrar(
        "APPROVE", entidad, "s-1", {}
    )
    await SqlAlchemyRegistradorAuditoria(db_session, None).registrar(
        "IMPORT", entidad, None, {}
    )
    repo = SqlAlchemyAuditoriaRepository(db_session)

    por_email, _ = await repo.list_pagina(
        FiltrosAuditoria(entidad=entidad, search=actor.email.split("@")[0]),
        offset=0,
        limit=10,
    )
    assert [r.accion for r in por_email] == ["APPROVE"]
    por_accion, _ = await repo.list_pagina(
        FiltrosAuditoria(entidad=entidad, search="import"), offset=0, limit=10
    )
    assert [r.accion for r in por_accion] == ["IMPORT"]
    assert por_accion[0].user_id is None
    por_entidad, total = await repo.list_pagina(
        FiltrosAuditoria(search=entidad.lower()), offset=0, limit=10
    )
    assert total == 2


async def test_registrador_nunca_lanza_si_la_sesion_falla() -> None:
    class _SesionRota:
        def add(self, _row: object) -> None:
            raise RuntimeError("sin conexión")

    registrador = SqlAlchemyRegistradorAuditoria(_SesionRota(), None)  # type: ignore[arg-type]
    await registrador.registrar("CREATE", "Employee", "1", {})


async def test_user_directory_lista_activos_ordenados_y_busca_por_ids(
    db_session: AsyncSession,
) -> None:
    prefijo = uuid.uuid4().hex[:6].upper()
    zeta = await _user(db_session, f"{prefijo} Zeta")
    alfa = await _user(db_session, f"{prefijo} Alfa")
    inactivo = await _user(db_session, f"{prefijo} Baja", activo=False)
    directorio = SqlAlchemyUserDirectory(db_session)

    activos = [u for u in await directorio.list_activos() if u.full_name.startswith(prefijo)]
    assert [u.id for u in activos] == [alfa.id, zeta.id]

    uno = await directorio.get_by_id(inactivo.id)
    assert uno is not None
    assert uno.email == inactivo.email
    assert await directorio.get_by_id(uuid.uuid4()) is None

    assert await directorio.get_by_ids([]) == {}
    varios = await directorio.get_by_ids([alfa.id, zeta.id, uuid.uuid4()])
    assert set(varios) == {alfa.id, zeta.id}
    assert varios[alfa.id].full_name == alfa.full_name


async def _asegurar_modulo_vacaciones(db_session: AsyncSession) -> None:
    if await db_session.get(Module, "vacaciones") is None:
        db_session.add(
            Module(key="vacaciones", label="Vacaciones", route="/vacaciones", icon="calendar")
        )
    if await db_session.get(Action, "manage") is None:
        db_session.add(Action(key="manage", label="Administrar"))
    await db_session.flush()
    if await db_session.get(ModuleAction, ("vacaciones", "manage")) is None:
        db_session.add(ModuleAction(module_key="vacaciones", action_key="manage"))
    await db_session.flush()


async def test_destinatarios_une_jefes_del_sector_y_admins_sin_duplicar_ni_inactivos(
    db_session: AsyncSession, sector_id: uuid.UUID
) -> None:
    await _asegurar_modulo_vacaciones(db_session)
    jefe = await _user(db_session, "Jefe Sector")
    admin = await _user(db_session, "Admin Vac")
    ambos = await _user(db_session, "Jefe y Admin")
    jefe_inactivo = await _user(db_session, "Jefe Inactivo", activo=False)
    jefe_otro_sector = await _user(db_session, "Jefe Otro")
    db_session.add_all(
        [
            UserModuleScope(
                user_id=jefe.id, module_key="vacaciones", scope_department_id=sector_id
            ),
            UserModuleScope(
                user_id=ambos.id, module_key="vacaciones", scope_department_id=sector_id
            ),
            UserModuleScope(
                user_id=jefe_inactivo.id, module_key="vacaciones", scope_department_id=sector_id
            ),
            UserModuleScope(
                user_id=jefe_otro_sector.id, module_key="vacaciones", scope_department_id=None
            ),
            PermissionGrant(user_id=admin.id, module_key="vacaciones", action_key="manage"),
            PermissionGrant(user_id=ambos.id, module_key="vacaciones", action_key="manage"),
        ]
    )
    await db_session.flush()

    emails = await SqlAlchemyDestinatariosNuevaSolicitud(db_session).emails(sector_id)

    assert len(emails) == 3  # deduplicado: "ambos" aparece una sola vez
    assert set(emails) == {jefe.email, ambos.email, admin.email}
