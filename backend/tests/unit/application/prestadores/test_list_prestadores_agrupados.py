import uuid
from datetime import date

from src.modules.prestadores.application.use_cases.list_prestadores_agrupados import (
    ListPrestadoresAgrupados,
    ListPrestadoresAgrupadosDependencies,
)
from src.modules.prestadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.repositories.user_provider import UserInfo
from tests.unit.domain.prestadores.fakes import (
    FakeAsignacionOverrideRepository,
    FakeContactoRepository,
    FakePrestadorRepository,
    FakeUserProvider,
)


def _prestador(
    *, siges_id: int, nombre: str, operador_id: uuid.UUID | None, activo: bool = True
) -> Prestador:
    return Prestador(
        id=uuid.uuid4(),
        siges_empresa_id=siges_id,
        den_comercial=nombre,
        razon_social=None,
        cuit=None,
        equipos=None,
        operador_id=operador_id,
        is_active=activo,
    )


def _deps(
    prestadores: FakePrestadorRepository,
    users: FakeUserProvider,
    overrides: FakeAsignacionOverrideRepository | None = None,
) -> ListPrestadoresAgrupadosDependencies:
    return ListPrestadoresAgrupadosDependencies(
        prestadores=prestadores,
        contactos=FakeContactoRepository(),
        users=users,
        overrides=overrides or FakeAsignacionOverrideRepository(),
    )


async def test_agrupa_por_operador_y_deja_sin_asignar_al_final() -> None:
    prestadores = FakePrestadorRepository()
    users = FakeUserProvider()

    mjvela_id = uuid.uuid4()
    users.users[mjvela_id] = UserInfo(id=mjvela_id, full_name="Maria Jose Vela", color="#BC2FFE")

    p_asignado = _prestador(siges_id=1, nombre="PST Bahia Blanca", operador_id=mjvela_id)
    p_sin_asignar = _prestador(siges_id=2, nombre="PST Catamarca", operador_id=None)
    prestadores.rows[p_asignado.id] = p_asignado
    prestadores.rows[p_sin_asignar.id] = p_sin_asignar

    resumen = await ListPrestadoresAgrupados(_deps(prestadores, users)).execute()

    assert resumen.total_prestadores == 2
    assert [g.operador_id for g in resumen.grupos] == [mjvela_id, None]
    assert resumen.grupos[0].operador_nombre == "Maria Jose Vela"
    assert resumen.grupos[0].operador_color == "#BC2FFE"
    assert resumen.grupos[1].operador_nombre is None
    assert resumen.sin_asignar == 1
    assert resumen.operadores_con_pst == 1


async def test_prestador_inactivo_no_cuenta_en_operadores_con_pst() -> None:
    prestadores = FakePrestadorRepository()
    users = FakeUserProvider()
    operador_id = uuid.uuid4()
    users.users[operador_id] = UserInfo(id=operador_id, full_name="Luna Torres", color="#FFC0CB")

    p_inactivo = _prestador(siges_id=1, nombre="PST Esquel", operador_id=operador_id, activo=False)
    prestadores.rows[p_inactivo.id] = p_inactivo

    resumen = await ListPrestadoresAgrupados(_deps(prestadores, users)).execute()

    assert resumen.total_prestadores == 1
    assert resumen.total_activos == 0
    assert resumen.operadores_con_pst == 0
    # el PST inactivo igual aparece agrupado (para poder reactivarlo desde la UI)
    assert len(resumen.grupos) == 1
    assert resumen.grupos[0].prestadores[0].is_active is False


async def test_pst_cubierto_por_override_vigente_agrupa_bajo_el_reemplazante() -> None:
    """El PST sigue con Prestador.operador_id=titular (asignación real), pero
    el tablero lo agrupa bajo quien lo cubre hoy (ver ADR-013)."""
    prestadores = FakePrestadorRepository()
    users = FakeUserProvider()
    titular_id = uuid.uuid4()
    reemplazante_id = uuid.uuid4()
    users.users[titular_id] = UserInfo(id=titular_id, full_name="Luna Torres")
    users.users[reemplazante_id] = UserInfo(id=reemplazante_id, full_name="Maria Jose Vela")

    pst = _prestador(siges_id=1, nombre="PST Rosario", operador_id=titular_id)
    prestadores.rows[pst.id] = pst

    overrides = FakeAsignacionOverrideRepository()
    override = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=titular_id,
        operador_reemplazante_id=reemplazante_id,
        desde=date(2026, 8, 1),
        hasta=date(2026, 8, 15),
        alcance="TOTAL",
        estado="ACTIVA",
        motivo=None,
        created_by_user_id=uuid.uuid4(),
    )
    overrides.rows[override.id] = override

    resumen = await ListPrestadoresAgrupados(_deps(prestadores, users, overrides)).execute(
        fecha=date(2026, 8, 5)
    )

    assert [g.operador_id for g in resumen.grupos] == [reemplazante_id]
    assert resumen.grupos[0].operador_nombre == "Maria Jose Vela"
    # el PST individual sigue mostrando el titular real, no el reemplazante
    assert resumen.grupos[0].prestadores[0].operador_id == titular_id
    assert resumen.grupos[0].prestadores[0].operador_nombre == "Luna Torres"


async def test_pst_cubierto_fuera_de_vigencia_agrupa_bajo_el_titular() -> None:
    prestadores = FakePrestadorRepository()
    users = FakeUserProvider()
    titular_id = uuid.uuid4()
    reemplazante_id = uuid.uuid4()
    users.users[titular_id] = UserInfo(id=titular_id, full_name="Luna Torres")

    pst = _prestador(siges_id=1, nombre="PST Rosario", operador_id=titular_id)
    prestadores.rows[pst.id] = pst

    overrides = FakeAsignacionOverrideRepository()
    override = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=titular_id,
        operador_reemplazante_id=reemplazante_id,
        desde=date(2026, 8, 1),
        hasta=date(2026, 8, 15),
        alcance="TOTAL",
        estado="ACTIVA",
        motivo=None,
        created_by_user_id=uuid.uuid4(),
    )
    overrides.rows[override.id] = override

    resumen = await ListPrestadoresAgrupados(_deps(prestadores, users, overrides)).execute(
        fecha=date(2026, 9, 1)
    )

    assert [g.operador_id for g in resumen.grupos] == [titular_id]
