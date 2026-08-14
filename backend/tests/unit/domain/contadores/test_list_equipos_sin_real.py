from datetime import UTC, date, datetime

import pytest

from src.modules.contadores.application.dtos.equipo_sin_real_anotado import OperadorAsignado
from src.modules.contadores.application.dtos.list_equipos_sin_real_request import (
    ListEquiposSinRealRequest,
)
from src.modules.contadores.application.use_cases.get_equipos_sin_real_resumen import (
    GetEquiposSinRealResumenUseCase,
)
from src.modules.contadores.application.use_cases.list_equipos_sin_real import (
    ListEquiposSinRealDependencies,
    ListEquiposSinRealUseCase,
)
from src.modules.contadores.domain.entities.equipo_sin_real import (
    EquipoSinReal,
    EquiposSinRealSnapshot,
)
from src.modules.contadores.domain.services.severidad_sin_real import severidad_por_meses

_CONSULTADO_EN = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)


def _equipo(
    serie: str,
    cliente: str,
    meses: int,
    *,
    id_empresa: int = 0,
    sucursal: str = "Central",
    modelo: str = "HP E52645",
    fecha_ultimo_real: date | None = date(2026, 1, 1),
    im: tuple[int, int, int] = (0, 0, 0),
) -> EquipoSinReal:
    return EquipoSinReal(
        id_maquina=abs(hash(serie)) % 100000,
        id_empresa_cliente=id_empresa,
        serie=serie,
        modelo=modelo,
        tecnologia="Mono",
        propiedad="CD1 (CDSA)",
        cliente=cliente,
        sucursal=sucursal,
        estado_maquina="Activa en Cliente",
        observaciones="",
        fecha_ultimo_real=fecha_ultimo_real,
        fecha_referencia=fecha_ultimo_real or date(2020, 1, 1),
        dias_sin_real=meses * 30,
        meses_sin_real=meses,
        im1=im[0],
        im2=im[1],
        im3=im[2],
    )


class _FakePort:
    def __init__(self, equipos: list[EquipoSinReal]) -> None:
        self._equipos = equipos
        self.refresh_calls: list[bool] = []

    async def list_equipos(self, *, force_refresh: bool = False) -> EquiposSinRealSnapshot:
        self.refresh_calls.append(force_refresh)
        return EquiposSinRealSnapshot(equipos=self._equipos, consultado_en=_CONSULTADO_EN)


class _FakeMapa:
    def __init__(self, mapa: dict[int, OperadorAsignado]) -> None:
        self._mapa = mapa

    async def build(self, *, hoy: date) -> dict[int, OperadorAsignado]:
        return self._mapa


_UNIVERSO = [
    _equipo("S1", "Banco Bice", 14, id_empresa=10, modelo="Samsung ML-3750"),
    _equipo("S2", "adecoagro", 7, id_empresa=20, sucursal="La Guarida"),
    _equipo("S3", "Calico", 3, id_empresa=30, im=(194, 232, 992)),
    _equipo("S4", "Felfort", 1, id_empresa=40, fecha_ultimo_real=None),
]

_MAPA = {
    10: OperadorAsignado(nombre="Victor Paez", color="#888200"),
    30: OperadorAsignado(nombre="Ana Gomez", color=None),
}


def _use_case(
    equipos: list[EquipoSinReal] = _UNIVERSO,
    mapa: dict[int, OperadorAsignado] | None = _MAPA,
) -> ListEquiposSinRealUseCase:
    return ListEquiposSinRealUseCase(
        ListEquiposSinRealDependencies(
            port=_FakePort(equipos),
            operador_mapa=None if mapa is None else _FakeMapa(mapa),  # type: ignore[arg-type]
        )
    )


@pytest.mark.asyncio
async def test_filtra_por_min_meses_y_ordena_meses_desc_por_default() -> None:
    result = await _use_case().execute(ListEquiposSinRealRequest())
    assert [a.equipo.serie for a in result.equipos] == ["S1", "S2", "S3"]
    assert result.consultado_en == _CONSULTADO_EN


@pytest.mark.asyncio
async def test_anota_operador_por_id_empresa_y_none_sin_cruce() -> None:
    result = await _use_case().execute(ListEquiposSinRealRequest(min_meses=1))
    por_serie = {a.equipo.serie: a.operador for a in result.equipos}
    assert por_serie["S1"] == OperadorAsignado(nombre="Victor Paez", color="#888200")
    assert por_serie["S2"] is None
    assert por_serie["S3"] == OperadorAsignado(nombre="Ana Gomez", color=None)


@pytest.mark.asyncio
async def test_sin_mapa_degrada_a_operador_none() -> None:
    result = await _use_case(mapa=None).execute(ListEquiposSinRealRequest(min_meses=1))
    assert all(a.operador is None for a in result.equipos)


@pytest.mark.asyncio
async def test_ordena_por_operador_asc_con_sin_operador_al_final() -> None:
    result = await _use_case().execute(
        ListEquiposSinRealRequest(min_meses=1, sort_by="operador", sort_dir="asc")
    )
    assert [a.equipo.serie for a in result.equipos] == ["S3", "S1", "S2", "S4"]


@pytest.mark.asyncio
async def test_ordena_por_cliente_asc_ignorando_mayusculas() -> None:
    result = await _use_case().execute(
        ListEquiposSinRealRequest(min_meses=1, sort_by="cliente", sort_dir="asc")
    )
    assert [a.equipo.cliente for a in result.equipos] == [
        "adecoagro",
        "Banco Bice",
        "Calico",
        "Felfort",
    ]


@pytest.mark.asyncio
async def test_busca_tambien_por_operador() -> None:
    use_case = _use_case()
    por_operador = await use_case.execute(ListEquiposSinRealRequest(min_meses=1, search="paez"))
    por_modelo = await use_case.execute(ListEquiposSinRealRequest(min_meses=1, search="ml-37"))
    assert [a.equipo.serie for a in por_operador.equipos] == ["S1"]
    assert [a.equipo.serie for a in por_modelo.equipos] == ["S1"]


@pytest.mark.asyncio
async def test_resumen_cuenta_por_severidad_y_nunca_real() -> None:
    resumen = await GetEquiposSinRealResumenUseCase(_FakePort(_UNIVERSO)).execute()
    assert (resumen.total, resumen.criticos, resumen.altos) == (4, 1, 1)
    assert (resumen.medios, resumen.bajos, resumen.nunca_real) == (1, 1, 1)


def test_severidad_umbrales() -> None:
    assert severidad_por_meses(12) == "critico"
    assert severidad_por_meses(6) == "alto"
    assert severidad_por_meses(3) == "medio"
    assert severidad_por_meses(2) == "bajo"


def test_imp_prom_3m_trunca_como_el_legacy() -> None:
    equipo = _equipo("S3", "Calico", 3, im=(194, 232, 992))
    assert equipo.imp_prom_3m == 472
