import uuid

from src.modules.prestadores.application.use_cases.list_prestadores_agrupados import (
    ListPrestadoresAgrupados,
    ListPrestadoresAgrupadosDependencies,
)
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.repositories.user_provider import UserInfo
from tests.unit.domain.prestadores.fakes import (
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
        operador_id=operador_id,
        is_active=activo,
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

    deps = ListPrestadoresAgrupadosDependencies(
        prestadores=prestadores, contactos=FakeContactoRepository(), users=users
    )
    resumen = await ListPrestadoresAgrupados(deps).execute()

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

    deps = ListPrestadoresAgrupadosDependencies(
        prestadores=prestadores, contactos=FakeContactoRepository(), users=users
    )
    resumen = await ListPrestadoresAgrupados(deps).execute()

    assert resumen.total_prestadores == 1
    assert resumen.total_activos == 0
    assert resumen.operadores_con_pst == 0
    # el PST inactivo igual aparece agrupado (para poder reactivarlo desde la UI)
    assert len(resumen.grupos) == 1
    assert resumen.grupos[0].prestadores[0].is_active is False
