"""Preview/apply del cálculo de distancias: ida+vuelta reales, total como
convención de facturación, preview sin efectos sobre tabla_km, apply sin
Google, preservación de umbral/observaciones y control de tope."""

from uuid import UUID, uuid4

import pytest

from src.modules.liquidaciones.application.use_cases.calcular_distancias_siges import (
    AplicarCalcularDistancias,
    CalcularDistanciasPorts,
    PreviewCalcularDistancias,
)
from src.modules.liquidaciones.domain.errors import (
    PreviewNoEncontradoError,
    TopeLlamadasGoogleError,
)
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
    SigesSucursalPropia,
)
from tests.unit.domain.liquidaciones.factories import make_prestador, make_tabla_km
from tests.unit.domain.liquidaciones.fakes import FakePrestadorRepository
from tests.unit.domain.liquidaciones.fakes_geolocalizacion import (
    FakeCalculoKmPreviewRepository,
    FakeGoogleMapsIdaVuelta,
    FakeSigesGeoGateway,
    FakeSucursalCoordenadasRepository,
    FakeTablaKmGeoRepository,
)

_BASE = (-38.7189846, -62.264305)
_DESTINO = (-37.0222087, -62.3782513)


def _sucursal_cliente(
    siges_id: int = 1,
    empresa: str = "Adecoagro",
    sucursal: str = "Las Horquetas",
    latitud: str | None = "-37,0222087",
    longitud: str | None = "-62,3782513",
) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=siges_id,
        empresa_nombre=empresa,
        sucursal_nombre=sucursal,
        domicilio="Ruta Nacional 33 KM 167",
        localidad="GUAMINI",
        provincia="Buenos Aires",
        latitud=latitud,
        longitud=longitud,
    )


def _armar(
    clientes: list[SigesSucursalCliente],
    tabla_km: FakeTablaKmGeoRepository | None = None,
    tramos: dict | None = None,
    tope: int = 200,
) -> tuple[PreviewCalcularDistancias, AplicarCalcularDistancias, CalcularDistanciasPorts, UUID]:
    prestador = make_prestador(siges_empresa_id=77, siges_base_sucursal_id=9)
    base_propia = SigesSucursalPropia(
        siges_sucursal_id=9, descripcion="Base", latitud="-38,7189846", longitud="-62,264305"
    )
    ports = CalcularDistanciasPorts(
        prestadores=FakePrestadorRepository({prestador.id: prestador}),
        tabla_km=tabla_km or FakeTablaKmGeoRepository(),
        siges=FakeSigesGeoGateway(clientes=clientes, propias=[base_propia]),
        google_maps=FakeGoogleMapsIdaVuelta(tramos or {_DESTINO: (199.294, 199.521)}),
        sucursal_coords=FakeSucursalCoordenadasRepository(),
        previews=FakeCalculoKmPreviewRepository(),
    )
    return (
        PreviewCalcularDistancias(ports, tope),
        AplicarCalcularDistancias(ports),
        ports,
        prestador.id,
    )


class TestPreview:
    @pytest.mark.asyncio
    async def test_fila_nueva_con_ida_vuelta_y_total(self) -> None:
        preview_uc, _, ports, prestador_id = _armar([_sucursal_cliente()])
        preview = await preview_uc.execute(prestador_id)
        assert len(preview.filas) == 1
        fila = preview.filas[0]
        assert fila.accion == "crear"
        assert fila.kms_ida == 199.294
        assert fila.kms_vuelta == 199.521
        assert fila.kms_total == pytest.approx(398.815)
        assert fila.aplica_viatico is True
        assert fila.kms_a_facturar == pytest.approx(398.815)
        assert fila.coords_origen == "siges"
        assert preview.elementos_google == 2
        # el preview NO toca tabla_km
        assert await ports.tabla_km.list_by_prestador(prestador_id) == []

    @pytest.mark.asyncio
    async def test_fila_existente_preserva_umbral_y_muestra_diff(self) -> None:
        preview_uc, _, ports, prestador_id = _armar([_sucursal_cliente()])
        existente = make_tabla_km(
            prestador_id=prestador_id,
            empresa_nombre="Adecoagro",
            sucursal_nombre="Las Horquetas",
            kms_recorrido=199.294,
            kms_a_facturar=199.294,
            umbral_viatico=20.0,
        )
        ports.tabla_km.rows[existente.id] = existente  # type: ignore[attr-defined]
        preview = await preview_uc.execute(prestador_id)
        fila = preview.filas[0]
        assert fila.accion == "actualizar"
        assert fila.umbral_viatico == 20.0
        assert fila.kms_recorrido_actual == 199.294
        assert fila.kms_total == pytest.approx(398.815)

    @pytest.mark.asyncio
    async def test_sin_coords_ni_resolucion_queda_sin_ubicar(self) -> None:
        sucursal = _sucursal_cliente(latitud=None, longitud=None)
        preview_uc, _, _, prestador_id = _armar([sucursal])
        preview = await preview_uc.execute(prestador_id)
        assert preview.sin_ubicar == 1
        assert preview.filas == ()
        assert preview.elementos_google == 0

    @pytest.mark.asyncio
    async def test_resolucion_geocode_ubica_al_destino(self) -> None:
        sucursal = _sucursal_cliente(latitud=None, longitud=None)
        preview_uc, _, ports, prestador_id = _armar([sucursal])
        await ports.sucursal_coords.upsert_pendiente(
            prestador_id=prestador_id,
            siges_sucursal_id=1,
            empresa_nombre="Adecoagro",
            sucursal_nombre="Las Horquetas",
            direccion_normalizada="x",
        )
        await ports.sucursal_coords.resolver(
            1,
            latitud=_DESTINO[0],
            longitud=_DESTINO[1],
            procedencia="geocode",
            formatted_address="RN33 KM 167",
        )
        preview = await preview_uc.execute(prestador_id)
        assert len(preview.filas) == 1
        assert preview.filas[0].coords_origen == "geocode"

    @pytest.mark.asyncio
    async def test_tope_excedido_no_llama_a_google(self) -> None:
        preview_uc, _, ports, prestador_id = _armar([_sucursal_cliente()], tope=1)
        with pytest.raises(TopeLlamadasGoogleError):
            await preview_uc.execute(prestador_id)
        assert ports.google_maps.lotes == []  # type: ignore[attr-defined]


class TestApply:
    @pytest.mark.asyncio
    async def test_apply_crea_sin_llamar_a_google(self) -> None:
        preview_uc, aplicar_uc, ports, prestador_id = _armar([_sucursal_cliente()])
        preview = await preview_uc.execute(prestador_id)
        lotes_pre = len(ports.google_maps.lotes)  # type: ignore[attr-defined]
        resultado = await aplicar_uc.execute(preview.id)
        assert resultado.creadas == 1
        assert len(ports.google_maps.lotes) == lotes_pre  # type: ignore[attr-defined]
        filas = await ports.tabla_km.list_by_prestador(prestador_id)
        assert filas[0].kms_recorrido == pytest.approx(398.815)
        assert filas[0].kms_ida == 199.294
        assert filas[0].kms_vuelta == 199.521
        assert filas[0].url_maps is not None and "waypoints=" in filas[0].url_maps
        # el preview aplicado se descarta
        assert await ports.previews.get_by_id(preview.id) is None

    @pytest.mark.asyncio
    async def test_apply_actualiza_preservando_observaciones_y_umbral(self) -> None:
        preview_uc, aplicar_uc, ports, prestador_id = _armar([_sucursal_cliente()])
        existente = make_tabla_km(
            prestador_id=prestador_id,
            empresa_nombre="Adecoagro",
            sucursal_nombre="Las Horquetas",
            observaciones="ruta compartida con PDS",
            umbral_viatico=20.0,
            kms_recorrido=199.294,
            kms_a_facturar=199.294,
        )
        ports.tabla_km.rows[existente.id] = existente  # type: ignore[attr-defined]
        preview = await preview_uc.execute(prestador_id)
        resultado = await aplicar_uc.execute(preview.id)
        assert resultado.actualizadas == 1
        actualizada = await ports.tabla_km.get_by_id(existente.id)
        assert actualizada is not None
        assert actualizada.observaciones == "ruta compartida con PDS"
        assert actualizada.umbral_viatico == 20.0
        assert actualizada.kms_recorrido == pytest.approx(398.815)

    @pytest.mark.asyncio
    async def test_apply_de_preview_inexistente_falla(self) -> None:
        _, aplicar_uc, _, _ = _armar([_sucursal_cliente()])
        with pytest.raises(PreviewNoEncontradoError):
            await aplicar_uc.execute(uuid4())
