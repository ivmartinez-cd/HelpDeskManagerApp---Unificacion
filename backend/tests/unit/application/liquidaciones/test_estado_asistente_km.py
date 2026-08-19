"""DiagnosticarAsistenteKm: el cerebro del wizard responde todo el estado del
flujo sin gastar Google — no recibe gateway de geocoding (garantía
estructural) y con prestador sin vínculo ni siquiera consulta Siges."""

import dataclasses
import uuid
from datetime import datetime
from uuid import UUID

import pytest

from src.modules.liquidaciones.application.use_cases.estado_asistente_km import (
    DiagnosticarAsistenteKm,
    EstadoAsistenteKmPorts,
)
from src.modules.liquidaciones.domain.entities.sucursal_coordenadas import SucursalCoordenadas
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.repositories.geocoding_gateway import GeocodeCandidato
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
    SigesSucursalPropia,
)
from tests.unit.domain.liquidaciones.factories import make_prestador
from tests.unit.domain.liquidaciones.fakes import FakePrestadorRepository
from tests.unit.domain.liquidaciones.fakes_geolocalizacion import (
    FakeGeocodeCacheRepository,
    FakeIncidentesActividad,
    FakeSigesGeoGateway,
    FakeSucursalCoordenadasRepository,
    FakeTablaKmGeoRepository,
)

_AHORA = datetime(2026, 1, 1)
_TOPE = 200
_CANDIDATO = GeocodeCandidato(
    formatted_address="Av. Callao 1337, CABA",
    latitud=-34.5935,
    longitud=-58.3927,
    location_type="ROOFTOP",
    tipos=("street_address",),
)
# >5 km del pin (-34,5/-58,4) → sospechoso.
_CANDIDATO_LEJOS = GeocodeCandidato(
    formatted_address="Otro lado",
    latitud=-34.6,
    longitud=-58.4,
    location_type="ROOFTOP",
    tipos=("street_address",),
)


class _SigesEspia(FakeSigesGeoGateway):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self.consultas = 0

    async def list_sucursales_de_prestador(
        self, siges_empresa_id: int
    ) -> list[SigesSucursalCliente]:
        self.consultas += 1
        return await super().list_sucursales_de_prestador(siges_empresa_id)

    async def list_sucursales_de_empresa(
        self, siges_empresa_id: int
    ) -> list[SigesSucursalPropia]:
        self.consultas += 1
        return await super().list_sucursales_de_empresa(siges_empresa_id)


def _sucursal(
    siges_id: int,
    *,
    empresa: str = "Dia %",
    sucursal: str | None = None,
    lat: str | None = "-34,5",
    lon: str | None = "-58,4",
    domicilio: str | None = "Avenida Callao 1337",
) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=siges_id,
        empresa_nombre=empresa,
        sucursal_nombre=sucursal or f"Tienda {siges_id}",
        domicilio=domicilio,
        localidad="CABA",
        provincia="Capital Federal",
        latitud=lat,
        longitud=lon,
    )


def _resolucion(
    prestador_id: UUID,
    siges_id: int,
    *,
    resuelta: bool,
    direccion: str | None = "dir cacheada",
) -> SucursalCoordenadas:
    return SucursalCoordenadas(
        id=uuid.uuid4(),
        prestador_id=prestador_id,
        siges_sucursal_id=siges_id,
        empresa_nombre="Dia %",
        sucursal_nombre=f"Tienda {siges_id}",
        direccion_normalizada=direccion,
        latitud=-34.5 if resuelta else None,
        longitud=-58.4 if resuelta else None,
        procedencia="geocode" if resuelta else None,
        formatted_address=None,
        fecha_resolucion=_AHORA if resuelta else None,
        created_at=_AHORA,
        updated_at=_AHORA,
    )


def _fila_km(
    prestador_id: UUID,
    *,
    empresa: str = "Dia %",
    sucursal: str = "Tienda 1",
    kms: float = 12.0,
    siges_sucursal_id: int | None = None,
) -> TablaKm:
    return TablaKm(
        id=uuid.uuid4(),
        prestador_id=prestador_id,
        spst_id=None,
        empresa_nombre=empresa,
        sucursal_nombre=sucursal,
        observaciones=None,
        domicilio_cliente=None,
        localidad_cliente=None,
        provincia_cliente=None,
        kms_recorrido=kms,
        umbral_viatico=30.0,
        aplica_viatico=False,
        kms_a_facturar=0.0,
        url_maps=None,
        created_at=_AHORA,
        updated_at=_AHORA,
        siges_sucursal_id=siges_sucursal_id,
    )


def _armar(
    *,
    vinculado: bool = True,
    base_id: int | None = 9,
    clientes: list[SigesSucursalCliente] | None = None,
    propias: list[SigesSucursalPropia] | None = None,
    filas: list[TablaKm] | None = None,
    resoluciones: list[SucursalCoordenadas] | None = None,
    cache: dict[str, list[GeocodeCandidato]] | None = None,
    activas: set[str] | None = None,
):
    prestador = make_prestador(
        siges_empresa_id=77 if vinculado else None,
        siges_base_sucursal_id=base_id,
    )
    siges = _SigesEspia(
        clientes=clientes or [],
        propias=propias
        if propias is not None
        else [SigesSucursalPropia(
            siges_sucursal_id=9, descripcion="Base", latitud="-38,7", longitud="-62,2"
        )],
    )
    coords = FakeSucursalCoordenadasRepository()
    for r in resoluciones or []:
        coords.rows[r.siges_sucursal_id] = _rekey_res(r, prestador.id)
    cache_repo = FakeGeocodeCacheRepository()
    cache_repo.rows.update(cache or {})
    filas_km = [
        f if f.prestador_id == prestador.id else _rekey(f, prestador.id)
        for f in (filas or [])
    ]
    ports = EstadoAsistenteKmPorts(
        prestadores=FakePrestadorRepository({prestador.id: prestador}),
        siges=siges,
        tabla_km=FakeTablaKmGeoRepository(filas_km),
        sucursal_coords=coords,
        geocode_cache=cache_repo,
        incidentes=FakeIncidentesActividad(
            activas if activas is not None else {c.empresa_nombre for c in clientes or []}
        ),
    )
    return DiagnosticarAsistenteKm(ports, _TOPE), siges, prestador.id


def _rekey(fila: TablaKm, prestador_id: UUID) -> TablaKm:
    return dataclasses.replace(fila, prestador_id=prestador_id)


def _rekey_res(r: SucursalCoordenadas, prestador_id: UUID) -> SucursalCoordenadas:
    return dataclasses.replace(r, prestador_id=prestador_id)


class TestDiagnosticarAsistenteKm:
    @pytest.mark.asyncio
    async def test_sin_vinculo_short_circuit_y_no_consulta_siges(self) -> None:
        use_case, siges, pid = _armar(vinculado=False, clientes=[_sucursal(1)])
        estado = await use_case.execute(pid)
        assert estado.vinculado_siges is False
        assert estado.sucursales_activas == 0
        assert estado.tope_por_corrida == _TOPE
        assert siges.consultas == 0

    @pytest.mark.asyncio
    async def test_sin_base_configurada(self) -> None:
        use_case, _, pid = _armar(base_id=None, clientes=[_sucursal(1)])
        estado = await use_case.execute(pid)
        assert estado.base_configurada is False
        assert estado.base_con_coordenadas is False

    @pytest.mark.asyncio
    async def test_base_sin_coordenadas(self) -> None:
        propias = [SigesSucursalPropia(
            siges_sucursal_id=9, descripcion="Base", latitud="0", longitud="0"
        )]
        use_case, _, pid = _armar(propias=propias, clientes=[_sucursal(1)])
        estado = await use_case.execute(pid)
        assert estado.base_configurada is True
        assert estado.base_con_coordenadas is False

    @pytest.mark.asyncio
    async def test_clasificacion_mixta_y_estimacion_distancias(self) -> None:
        # 1: pin Siges → ubicable · 2 y 3: sin pin ni resolución → sin coords
        clientes = [
            _sucursal(1),
            _sucursal(2, lat=None, lon=None),
            _sucursal(3, lat=None, lon=None),
        ]
        use_case, _, pid = _armar(clientes=clientes)
        estado = await use_case.execute(pid)
        assert estado.sucursales_activas == 3
        assert estado.sin_coordenadas == 2
        assert estado.estimacion_distancias == 2  # solo la 1 es ubicable

    @pytest.mark.asyncio
    async def test_resolucion_local_hace_ubicable(self) -> None:
        clientes = [_sucursal(2, lat=None, lon=None)]
        resuelta = _resolucion(uuid.uuid4(), 2, resuelta=True)
        use_case, _, pid = _armar(clientes=clientes, resoluciones=[resuelta])
        estado = await use_case.execute(pid)
        assert estado.sin_coordenadas == 0
        assert estado.estimacion_distancias == 2

    @pytest.mark.asyncio
    async def test_estimacion_geocodificar_respeta_cache(self) -> None:
        # dos sin pin: una con cache (aunque ZERO_RESULTS) no estima, la otra sí
        clientes = [
            _sucursal(1, lat=None, lon=None, domicilio="Calle Uno 1"),
            _sucursal(2, lat=None, lon=None, domicilio="Calle Dos 2"),
        ]
        cache = {"Calle Uno 1, CABA, Capital Federal, Argentina": []}
        use_case, _, pid = _armar(clientes=clientes, cache=cache)
        estado = await use_case.execute(pid)
        assert estado.estimacion_geocodificar == 1

    @pytest.mark.asyncio
    async def test_pines_cacheados_y_estimacion_auditar(self) -> None:
        # 1: con pin + cache lejano → sospechoso · 2: con pin + cache cercano →
        # no sospechoso · 3: con pin sin cache → estima auditoría
        clientes = [
            _sucursal(1, domicilio="Calle Uno 1"),
            _sucursal(2, domicilio="Calle Dos 2"),
            _sucursal(3, domicilio="Calle Tres 3"),
        ]
        cache = {
            "Calle Uno 1, CABA, Capital Federal, Argentina": [_CANDIDATO_LEJOS],
            "Calle Dos 2, CABA, Capital Federal, Argentina": [
                GeocodeCandidato(
                    formatted_address="cerca",
                    latitud=-34.500001,
                    longitud=-58.400001,
                    location_type="ROOFTOP",
                    tipos=("street_address",),
                )
            ],
        }
        use_case, _, pid = _armar(clientes=clientes, cache=cache)
        estado = await use_case.execute(pid)
        assert estado.pines_sospechosos_cacheados == 1
        assert estado.estimacion_auditar_pines == 1

    @pytest.mark.asyncio
    async def test_ex_cliente_solo_cuenta_como_ex(self) -> None:
        clientes = [_sucursal(1), _sucursal(2, empresa="Ex Cliente SA", lat=None, lon=None)]
        use_case, _, pid = _armar(clientes=clientes, activas={"Dia %"})
        estado = await use_case.execute(pid)
        assert estado.ex_clientes == 1
        assert estado.sucursales_activas == 1
        assert estado.sin_coordenadas == 0  # la ex no cuenta

    @pytest.mark.asyncio
    async def test_nuevas_ambiguas_sin_km_y_no_encontradas(self) -> None:
        clientes = [_sucursal(1, sucursal="Tienda 1"), _sucursal(2, sucursal="Tienda 2")]
        filas = [
            _fila_km(uuid.uuid4(), sucursal="Tienda 1", kms=0.0),
            _fila_km(uuid.uuid4(), empresa="Renombrada", sucursal="X"),
        ]
        ambigua = _resolucion(uuid.uuid4(), 5, resuelta=False, direccion="dir ambigua")
        cache = {"dir ambigua": [_CANDIDATO, _CANDIDATO_LEJOS]}
        use_case, _, pid = _armar(
            clientes=clientes, filas=filas, resoluciones=[ambigua], cache=cache
        )
        estado = await use_case.execute(pid)
        assert estado.sucursales_nuevas_por_importar == 1  # Tienda 2
        assert estado.filas_tabla_km == 2
        assert estado.filas_sin_km == 1
        assert estado.no_encontradas_en_siges == 1  # "Renombrada"
        assert estado.ambiguas_pendientes == 1

    @pytest.mark.asyncio
    async def test_fila_vinculada_por_id_no_cuenta_como_no_encontrada(self) -> None:
        # Matching N1/N2: el nombre local no matchea textualmente (símbolo/
        # abreviatura distinta) pero la fila ya tiene siges_sucursal_id — no
        # es "no encontrada", está vinculada por id.
        clientes = [_sucursal(1, sucursal="Tienda 1")]
        filas = [
            _fila_km(uuid.uuid4(), sucursal="Tienda Uno", siges_sucursal_id=1),
        ]
        use_case, _, pid = _armar(clientes=clientes, filas=filas)
        estado = await use_case.execute(pid)
        assert estado.no_encontradas_en_siges == 0
