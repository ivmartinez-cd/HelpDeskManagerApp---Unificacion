"""Fichas de clientes nuevos: entidad, alta/edición con regla de ficha abierta
única por cliente, listado anotado con Siges (con y sin gateway) y candidatos
filtrados contra las fichas existentes."""

import uuid
from datetime import date

import pytest

from src.modules.contadores.application.dtos.cliente_nuevo_dtos import ClienteNuevoRequest
from src.modules.contadores.application.use_cases.create_cliente_nuevo import (
    CreateClienteNuevoUseCase,
)
from src.modules.contadores.application.use_cases.list_clientes_nuevos import (
    ListCandidatosClientesNuevosUseCase,
    ListClientesNuevosDependencies,
    ListClientesNuevosUseCase,
)
from src.modules.contadores.application.use_cases.update_cliente_nuevo import (
    DeleteClienteNuevoUseCase,
    UpdateClienteNuevoUseCase,
)
from src.modules.contadores.domain.entities.cliente_nuevo import (
    ESTADO_CERRADO,
    ESTADO_ESPERANDO_INSTALACION,
    ESTADO_STC_PENDIENTE,
    CandidatoClienteNuevo,
    ClienteNuevo,
    ResumenSigesClienteNuevo,
    listo_para_stc,
)
from src.modules.contadores.domain.errors import (
    ClienteNuevoNotFoundError,
    DuplicateClienteNuevoError,
    InvalidClienteNuevoError,
    InvalidEstadoClienteNuevoError,
)
from src.modules.contadores.domain.services.rubro_empresa_admin import (
    RUBRO_CARTELERIA,
    RUBRO_DESCONOCIDO,
    RUBRO_IMPRESION,
    rubro_por_empresa_admin,
)
from src.shared.domain.errors import ExternalServiceError

_USER = uuid.uuid4()


class InMemoryClienteNuevoRepository:
    def __init__(self) -> None:
        self.fichas: dict[uuid.UUID, ClienteNuevo] = {}

    async def get_by_id(self, ficha_id: uuid.UUID) -> ClienteNuevo | None:
        return self.fichas.get(ficha_id)

    async def get_abierta_by_cliente(self, cliente: str) -> ClienteNuevo | None:
        for f in self.fichas.values():
            if f.cliente.lower() == cliente.strip().lower() and f.abierta:
                return f
        return None

    async def list_all(self) -> list[ClienteNuevo]:
        return list(self.fichas.values())

    async def list_siges_empresa_ids(self) -> set[int]:
        return {f.siges_empresa_id for f in self.fichas.values() if f.siges_empresa_id}

    async def add(self, ficha: ClienteNuevo) -> None:
        self.fichas[ficha.id] = ficha

    async def save(self, ficha: ClienteNuevo) -> None:
        self.fichas[ficha.id] = ficha

    async def delete(self, ficha_id: uuid.UUID) -> None:
        self.fichas.pop(ficha_id, None)


class FakeSiges:
    def __init__(
        self,
        resumen: dict[int, ResumenSigesClienteNuevo] | None = None,
        candidatos: list[CandidatoClienteNuevo] | None = None,
        falla: bool = False,
    ) -> None:
        self._resumen = resumen or {}
        self._candidatos = candidatos or []
        self._falla = falla

    async def resumen_por_empresa(
        self, empresa_ids: frozenset[int], *, force_refresh: bool = False
    ) -> dict[int, ResumenSigesClienteNuevo]:
        if self._falla:
            raise ExternalServiceError("MERCURIO caído")
        return {k: v for k, v in self._resumen.items() if k in empresa_ids}

    async def candidatos_desde(
        self, firmado_desde: date, *, force_refresh: bool = False
    ) -> list[CandidatoClienteNuevo]:
        return self._candidatos


def _request(**overrides: object) -> ClienteNuevoRequest:
    base: dict[str, object] = {
        "cliente": "EXPRESO BILETTA",
        "siges_empresa_id": 1416,
        "contrato_nro": "SOD36CDSI00837",
        "fecha_firma": date(2026, 7, 28),
        "vendedor": "AV",
        "operador_id": "marodriguez",
        "implementacion_servicio": "MPS",
        "fecha_estimada_implementacion": date(2026, 8, 20),
        "fecha_estimada_primera_facturacion": date(2026, 10, 1),
        "dia_corte": None,
        "equipos_previstos": 10,
        "estado": ESTADO_ESPERANDO_INSTALACION,
        "stc_enviado_el": None,
        "notas": None,
    }
    base.update(overrides)
    return ClienteNuevoRequest(**base)  # type: ignore[arg-type]


def _resumen(empresa_id: int = 1416, instalados: int = 11) -> ResumenSigesClienteNuevo:
    return ResumenSigesClienteNuevo(
        empresa_id=empresa_id,
        equipos_instalados=instalados,
        instalas=4,
        primera_instalacion=date(2026, 8, 6),
        ultima_instalacion=date(2026, 8, 21),
        equipos_con_toma=11,
        contrato_nro="SOD36CDSI00837",
        fecha_firma=date(2026, 7, 28),
        vendedor="Adrián Vanrell",
        rubro=RUBRO_IMPRESION,
    )


# --- entidad -----------------------------------------------------------------


def test_entidad_valida_estado_dia_corte_y_cliente() -> None:
    with pytest.raises(InvalidEstadoClienteNuevoError):
        ClienteNuevo(id=uuid.uuid4(), cliente="X", created_by_user_id=_USER, estado="RARO")
    with pytest.raises(InvalidClienteNuevoError):
        ClienteNuevo(id=uuid.uuid4(), cliente="X", created_by_user_id=_USER, dia_corte=32)
    with pytest.raises(InvalidClienteNuevoError):
        ClienteNuevo(id=uuid.uuid4(), cliente="   ", created_by_user_id=_USER)


def test_listo_para_stc_solo_esperando_y_con_instalados_suficientes() -> None:
    ficha = ClienteNuevo(
        id=uuid.uuid4(), cliente="X", created_by_user_id=_USER, equipos_previstos=10
    )
    assert listo_para_stc(ficha, _resumen(instalados=11)) is True
    assert listo_para_stc(ficha, _resumen(instalados=3)) is False
    assert listo_para_stc(ficha, None) is False
    ficha.equipos_previstos = None
    assert listo_para_stc(ficha, _resumen(instalados=1)) is True
    ficha.estado = ESTADO_STC_PENDIENTE
    assert listo_para_stc(ficha, _resumen(instalados=11)) is False


def test_rubro_por_empresa_admin() -> None:
    assert rubro_por_empresa_admin(121) == RUBRO_IMPRESION
    assert rubro_por_empresa_admin(681) == RUBRO_CARTELERIA
    assert rubro_por_empresa_admin(None) == RUBRO_DESCONOCIDO


# --- alta / edición / baja ---------------------------------------------------


@pytest.mark.asyncio
async def test_crear_rechaza_segunda_ficha_abierta_del_mismo_cliente() -> None:
    repo = InMemoryClienteNuevoRepository()
    use_case = CreateClienteNuevoUseCase(repo)
    creada = await use_case.execute(_request(), created_by_user_id=_USER)
    assert creada.estado == ESTADO_ESPERANDO_INSTALACION
    assert creada.listo_para_stc is False

    with pytest.raises(DuplicateClienteNuevoError):
        await use_case.execute(_request(cliente="  expreso biletta "), created_by_user_id=_USER)


@pytest.mark.asyncio
async def test_crear_permite_nueva_ficha_si_la_anterior_esta_cerrada() -> None:
    repo = InMemoryClienteNuevoRepository()
    use_case = CreateClienteNuevoUseCase(repo)
    primera = await use_case.execute(_request(estado=ESTADO_CERRADO), created_by_user_id=_USER)
    segunda = await use_case.execute(_request(), created_by_user_id=_USER)
    assert primera.id != segunda.id
    assert len(repo.fichas) == 2


@pytest.mark.asyncio
async def test_editar_aplica_campos_y_valida() -> None:
    repo = InMemoryClienteNuevoRepository()
    creada = await CreateClienteNuevoUseCase(repo).execute(_request(), created_by_user_id=_USER)
    editada = await UpdateClienteNuevoUseCase(repo).execute(
        creada.id,
        _request(estado=ESTADO_STC_PENDIENTE, dia_corte=25, notas="  STC armado  "),
    )
    assert editada.estado == ESTADO_STC_PENDIENTE
    assert editada.dia_corte == 25
    assert editada.notas == "STC armado"

    with pytest.raises(InvalidClienteNuevoError):
        await UpdateClienteNuevoUseCase(repo).execute(creada.id, _request(dia_corte=0))
    with pytest.raises(ClienteNuevoNotFoundError):
        await UpdateClienteNuevoUseCase(repo).execute(uuid.uuid4(), _request())


@pytest.mark.asyncio
async def test_editar_rechaza_renombrar_a_otro_cliente_con_ficha_abierta() -> None:
    repo = InMemoryClienteNuevoRepository()
    crear = CreateClienteNuevoUseCase(repo)
    await crear.execute(_request(cliente="SWEET DREAM"), created_by_user_id=_USER)
    otra = await crear.execute(_request(cliente="FURLONG"), created_by_user_id=_USER)
    with pytest.raises(DuplicateClienteNuevoError):
        await UpdateClienteNuevoUseCase(repo).execute(otra.id, _request(cliente="sweet dream"))


@pytest.mark.asyncio
async def test_borrar_existente_y_no_existente() -> None:
    repo = InMemoryClienteNuevoRepository()
    creada = await CreateClienteNuevoUseCase(repo).execute(_request(), created_by_user_id=_USER)
    await DeleteClienteNuevoUseCase(repo).execute(creada.id)
    assert repo.fichas == {}
    with pytest.raises(ClienteNuevoNotFoundError):
        await DeleteClienteNuevoUseCase(repo).execute(creada.id)


# --- listado anotado ---------------------------------------------------------


@pytest.mark.asyncio
async def test_listar_anota_siges_solo_a_fichas_cruzadas() -> None:
    repo = InMemoryClienteNuevoRepository()
    crear = CreateClienteNuevoUseCase(repo)
    await crear.execute(_request(), created_by_user_id=_USER)
    await crear.execute(
        _request(cliente="BP", siges_empresa_id=None, equipos_previstos=None),
        created_by_user_id=_USER,
    )
    deps = ListClientesNuevosDependencies(repo=repo, siges=FakeSiges({1416: _resumen()}))
    resultados = await ListClientesNuevosUseCase(deps).execute()
    por_cliente = {r.cliente: r for r in resultados}
    assert por_cliente["EXPRESO BILETTA"].siges is not None
    assert por_cliente["EXPRESO BILETTA"].siges.equipos_instalados == 11
    assert por_cliente["EXPRESO BILETTA"].listo_para_stc is True
    assert por_cliente["BP"].siges is None
    assert por_cliente["BP"].listo_para_stc is False


@pytest.mark.asyncio
async def test_listar_degrada_sin_siges_o_si_siges_falla() -> None:
    repo = InMemoryClienteNuevoRepository()
    await CreateClienteNuevoUseCase(repo).execute(_request(), created_by_user_id=_USER)
    sin_gateway = ListClientesNuevosDependencies(repo=repo, siges=None)
    assert (await ListClientesNuevosUseCase(sin_gateway).execute())[0].siges is None
    caido = ListClientesNuevosDependencies(repo=repo, siges=FakeSiges(falla=True))
    assert (await ListClientesNuevosUseCase(caido).execute())[0].siges is None


# --- candidatos --------------------------------------------------------------


@pytest.mark.asyncio
async def test_candidatos_excluye_empresas_con_ficha() -> None:
    repo = InMemoryClienteNuevoRepository()
    await CreateClienteNuevoUseCase(repo).execute(_request(), created_by_user_id=_USER)
    candidatos = [
        CandidatoClienteNuevo(
            1416, "EXPRESO BILETTA", "SOD36CDSI00837", date(2026, 7, 28), "AV", RUBRO_IMPRESION, 11
        ),
        CandidatoClienteNuevo(
            1417, "SWEET DREAM", "COP36DIRAR00838", date(2026, 8, 10), "MR", RUBRO_CARTELERIA, 1
        ),
        CandidatoClienteNuevo(
            1411, "FURLONG", "FURLONG DEMO", date(2026, 7, 1), "AV", RUBRO_IMPRESION, 0
        ),
    ]
    deps = ListClientesNuevosDependencies(repo=repo, siges=FakeSiges(candidatos=candidatos))
    result = await ListCandidatosClientesNuevosUseCase(deps).execute(
        hoy=date(2026, 8, 21), dias=120
    )
    # SWEET DREAM es cartelería (CD4): no es de Contadores; solo quedan los de impresión
    # sin ficha (BILETTA ya tiene ficha).
    assert [c.empresa_id for c in result.candidatos] == [1411]
    assert result.firmado_desde == date(2026, 4, 23)

    sin_siges = ListClientesNuevosDependencies(repo=repo, siges=None)
    vacio = await ListCandidatosClientesNuevosUseCase(sin_siges).execute(hoy=date(2026, 8, 21))
    assert vacio.candidatos == []
