"""ABMs de catálogos: cargos, sectores, feriados y exclusiones."""

import uuid
from datetime import date

import pytest

from src.modules.vacaciones.application.dtos.gestion_dtos import (
    CargoCommand,
    FeriadoCommand,
    SectorCommand,
)
from src.modules.vacaciones.application.use_cases.gestionar_cargos import (
    CreateCargo,
    DeleteCargo,
    GestionCargosDependencies,
    ListCargos,
    UpdateCargo,
)
from src.modules.vacaciones.application.use_cases.gestionar_exclusiones import (
    CrearExclusion,
    EliminarExclusion,
    ExclusionesDependencies,
    ListarExclusiones,
)
from src.modules.vacaciones.application.use_cases.gestionar_feriados import (
    CreateFeriado,
    DeleteFeriado,
    GestionFeriadosDependencies,
    ImportarFeriados,
    ImportarFeriadosDependencies,
    ListFeriados,
    UpdateFeriado,
)
from src.modules.vacaciones.application.use_cases.gestionar_sectores import (
    CreateSector,
    DeleteSector,
    GestionSectoresDependencies,
    ListSectores,
    UpdateSector,
)
from src.modules.vacaciones.domain.entities.cargo import Cargo
from src.modules.vacaciones.domain.entities.exclusion import Exclusion
from src.modules.vacaciones.domain.entities.feriado import Feriado
from src.modules.vacaciones.domain.entities.sector import Sector
from src.modules.vacaciones.domain.errors import (
    CargoConEmpleadosError,
    NombreDuplicadoError,
    SectorConEmpleadosError,
)
from src.modules.vacaciones.domain.repositories.feriados_externos import FeriadoImportado
from src.modules.vacaciones.domain.repositories.sector_manager_repository import JefeSector
from src.modules.vacaciones.domain.repositories.user_directory import UserInfo
from src.shared.domain.errors import NotFoundError, ValidationError
from tests.unit.application.vacaciones.fakes import (
    FakeCargoRepo,
    FakeEmpleadoRepo,
    FakeExclusionRepo,
    FakeFeriadoRepo,
    FakeFeriadosExternosProvider,
    FakeSectorManagerRepo,
    FakeSectorRepo,
    FakeUserDirectory,
)
from tests.unit.domain.vacaciones.factories import make_empleado

# ------------------------------------------------------------------- cargos


def _cargo(name: str = "Técnico") -> Cargo:
    return Cargo(id=uuid.uuid4(), name=name, max_simultaneos=2)


async def test_cargos_abm_completo() -> None:
    tecnico = _cargo()
    repo = FakeCargoRepo([tecnico])
    repo.empleados_por_cargo[tecnico.id] = 3
    deps = GestionCargosDependencies(cargos=repo)

    listado = await ListCargos(deps).execute()
    assert [(d.cargo.name, d.empleados_count) for d in listado] == [("Técnico", 3)]

    nuevo = await CreateCargo(deps).execute(CargoCommand(name="Admin", max_simultaneos=None))
    assert await repo.get_by_id(nuevo.id) is nuevo

    actualizado = await UpdateCargo(deps).execute(
        nuevo.id, CargoCommand(name="Administrativo", max_simultaneos=1)
    )
    assert actualizado.name == "Administrativo" and actualizado.max_simultaneos == 1

    await DeleteCargo(deps).execute(nuevo.id)
    assert await repo.get_by_id(nuevo.id) is None


async def test_cargos_rechaza_duplicados_inexistentes_y_con_empleados() -> None:
    tecnico = _cargo()
    repo = FakeCargoRepo([tecnico, _cargo("Otro")])
    repo.empleados_por_cargo[tecnico.id] = 3
    deps = GestionCargosDependencies(cargos=repo)

    with pytest.raises(NombreDuplicadoError):
        await CreateCargo(deps).execute(CargoCommand(name="Técnico", max_simultaneos=None))
    with pytest.raises(NombreDuplicadoError):
        otro = await repo.get_by_name("Otro")
        assert otro is not None
        await UpdateCargo(deps).execute(otro.id, CargoCommand(name="Técnico", max_simultaneos=None))
    with pytest.raises(NotFoundError):
        await UpdateCargo(deps).execute(uuid.uuid4(), CargoCommand(name="X", max_simultaneos=None))
    with pytest.raises(NotFoundError):
        await DeleteCargo(deps).execute(uuid.uuid4())
    with pytest.raises(CargoConEmpleadosError):
        await DeleteCargo(deps).execute(tecnico.id)


# ------------------------------------------------------------------ sectores


def _sector(name: str = "Mesa") -> Sector:
    return Sector(id=uuid.uuid4(), name=name, color="#123456", is_active=True)


async def test_sectores_list_incluye_jefes_y_conteo() -> None:
    sector = _sector()
    jefe = UserInfo(id=uuid.uuid4(), email="jefa@cd.com", full_name="Jefa")
    empleados = FakeEmpleadoRepo([make_empleado(department_id=sector.id)])
    deps = GestionSectoresDependencies(
        sectores=FakeSectorRepo([sector]),
        empleados=empleados,
        sector_manager=FakeSectorManagerRepo(
            [JefeSector(user_id=jefe.id, department_id=sector.id)]
        ),
        users=FakeUserDirectory([jefe]),
    )

    listado = await ListSectores(deps).execute()

    assert len(listado) == 1
    assert listado[0].empleados_count == 1
    assert [j.full_name for j in listado[0].jefes] == ["Jefa"]


async def test_sectores_abm_reasigna_jefe_y_valida() -> None:
    sector = _sector()
    manager = FakeSectorManagerRepo()
    deps = GestionSectoresDependencies(
        sectores=FakeSectorRepo([sector]),
        empleados=FakeEmpleadoRepo([]),
        sector_manager=manager,
        users=FakeUserDirectory(),
    )

    jefe_1, jefe_2 = uuid.uuid4(), uuid.uuid4()
    nuevo = await CreateSector(deps).execute(
        SectorCommand(name="Depósito", color="#fff", jefe_user_id=jefe_1)
    )
    assert await manager.get_sector_de_usuario(jefe_1) == nuevo.id

    await UpdateSector(deps).execute(
        nuevo.id, SectorCommand(name="Depósito Norte", color="#000", jefe_user_id=jefe_2)
    )
    assert await manager.get_sector_de_usuario(jefe_1) is None
    assert await manager.get_sector_de_usuario(jefe_2) == nuevo.id

    with pytest.raises(NombreDuplicadoError):
        await CreateSector(deps).execute(
            SectorCommand(name="Depósito Norte", color="#fff", jefe_user_id=None)
        )
    with pytest.raises(NombreDuplicadoError):
        await UpdateSector(deps).execute(
            sector.id, SectorCommand(name="Depósito Norte", color="#fff", jefe_user_id=None)
        )
    with pytest.raises(NotFoundError):
        await UpdateSector(deps).execute(
            uuid.uuid4(), SectorCommand(name="X", color="#fff", jefe_user_id=None)
        )

    await DeleteSector(deps).execute(nuevo.id)
    assert await manager.get_sector_de_usuario(jefe_2) is None


async def test_sector_con_empleados_activos_no_se_borra() -> None:
    sector = _sector()
    deps = GestionSectoresDependencies(
        sectores=FakeSectorRepo([sector]),
        empleados=FakeEmpleadoRepo([make_empleado(department_id=sector.id)]),
        sector_manager=FakeSectorManagerRepo(),
        users=FakeUserDirectory(),
    )
    with pytest.raises(SectorConEmpleadosError):
        await DeleteSector(deps).execute(sector.id)
    with pytest.raises(NotFoundError):
        await DeleteSector(deps).execute(uuid.uuid4())


# ------------------------------------------------------------------ feriados


def _feriado(fecha: date, name: str = "Feriado") -> Feriado:
    return Feriado(id=uuid.uuid4(), name=name, date=fecha, deducts_vacation=False)


async def test_feriados_abm_y_validaciones() -> None:
    navidad = _feriado(date(2026, 12, 25), "Navidad")
    repo = FakeFeriadoRepo([navidad])
    deps = GestionFeriadosDependencies(feriados=repo)

    assert await ListFeriados(deps).execute() == [navidad]

    nuevo = await CreateFeriado(deps).execute(
        FeriadoCommand(name="Año Nuevo", fecha=date(2027, 1, 1), deducts_vacation=False)
    )
    with pytest.raises(NombreDuplicadoError):
        await CreateFeriado(deps).execute(
            FeriadoCommand(name="Duplicado", fecha=date(2027, 1, 1), deducts_vacation=False)
        )

    actualizado = await UpdateFeriado(deps).execute(
        nuevo.id,
        FeriadoCommand(name="Año Nuevo 2027", fecha=date(2027, 1, 1), deducts_vacation=True),
    )
    assert actualizado.deducts_vacation is True
    with pytest.raises(NombreDuplicadoError):
        await UpdateFeriado(deps).execute(
            nuevo.id,
            FeriadoCommand(name="Choca", fecha=date(2026, 12, 25), deducts_vacation=False),
        )
    with pytest.raises(NotFoundError):
        await UpdateFeriado(deps).execute(
            uuid.uuid4(), FeriadoCommand(name="X", fecha=date(2027, 2, 1), deducts_vacation=False)
        )

    await DeleteFeriado(deps).execute(nuevo.id)
    assert await repo.get_by_id(nuevo.id) is None
    with pytest.raises(NotFoundError):
        await DeleteFeriado(deps).execute(nuevo.id)


async def test_importar_feriados_hace_upsert_por_fecha() -> None:
    existente = _feriado(date(2026, 12, 25), "Navidad vieja")
    repo = FakeFeriadoRepo([existente])
    deps = ImportarFeriadosDependencies(
        feriados=repo,
        provider=FakeFeriadosExternosProvider(
            [
                FeriadoImportado(fecha=date(2026, 12, 25), nombre="Navidad"),
                FeriadoImportado(fecha=date(2026, 7, 9), nombre="Independencia"),
            ]
        ),
    )

    resultado = await ImportarFeriados(deps).execute(2026)

    assert (resultado.year, resultado.count) == (2026, 2)
    assert len(repo.items) == 2  # upsert: pisa el nombre, no duplica la fecha
    assert existente.name == "Navidad"


# --------------------------------------------------------------- exclusiones


async def test_exclusiones_crear_listar_y_eliminar() -> None:
    ana = make_empleado(first_name="Ana", last_name="A")
    beto = make_empleado(first_name="Beto", last_name="B")
    repo = FakeExclusionRepo()
    deps = ExclusionesDependencies(
        exclusiones=repo, empleados=FakeEmpleadoRepo([ana, beto])
    )

    exclusion = await CrearExclusion(deps).execute(beto.id, ana.id)  # se normaliza a<b
    assert exclusion.empleado_a_id < exclusion.empleado_b_id

    listado = await ListarExclusiones(deps).execute()
    assert {listado[0].empleado_a_nombre, listado[0].empleado_b_nombre} == {"Ana A", "Beto B"}

    with pytest.raises(ValidationError):
        await CrearExclusion(deps).execute(ana.id, ana.id)
    with pytest.raises(NombreDuplicadoError):
        await CrearExclusion(deps).execute(ana.id, beto.id)

    await EliminarExclusion(deps).execute(exclusion.id)
    assert repo.items == []
    with pytest.raises(NotFoundError):
        await EliminarExclusion(deps).execute(exclusion.id)


async def test_exclusiones_con_empleado_borrado_muestra_nombre_vacio() -> None:
    ana = make_empleado(first_name="Ana", last_name="A")
    fantasma = uuid.uuid4()
    a, b = sorted([ana.id, fantasma])
    par = Exclusion(id=uuid.uuid4(), empleado_a_id=a, empleado_b_id=b)
    deps = ExclusionesDependencies(
        exclusiones=FakeExclusionRepo([par]),
        empleados=FakeEmpleadoRepo([ana]),
    )

    listado = await ListarExclusiones(deps).execute()

    assert "" in {listado[0].empleado_a_nombre, listado[0].empleado_b_nombre}
