"""Fakes en memoria de los puertos de geolocalización (geocoding, cache,
resoluciones de coordenadas, previews de cálculo y matrix ida/vuelta)."""

import dataclasses
import uuid
from datetime import datetime
from uuid import UUID

from src.modules.liquidaciones.domain.entities.calculo_km_preview import (
    CalculoKmPreview,
    PreviewFila,
)
from src.modules.liquidaciones.domain.entities.cuadricula_base_map import CuadriculaBaseMap
from src.modules.liquidaciones.domain.entities.sucursal_coordenadas import SucursalCoordenadas
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.repositories.geocoding_gateway import GeocodeCandidato
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
    SigesSucursalPropia,
)

_AHORA = datetime(2026, 1, 1)


class FakeSigesGeoGateway:
    """Solo los datasets que usan los use cases de geolocalización."""

    def __init__(
        self,
        clientes: list[SigesSucursalCliente] | None = None,
        propias: list[SigesSucursalPropia] | None = None,
    ) -> None:
        self.clientes = clientes or []
        self.propias = propias or []

    async def list_sucursales_de_prestador(
        self, siges_empresa_id: int
    ) -> list[SigesSucursalCliente]:
        return list(self.clientes)

    async def list_sucursales_de_empresa(
        self, siges_empresa_id: int
    ) -> list[SigesSucursalPropia]:
        return list(self.propias)


class FakeGeocodingGateway:
    def __init__(self, por_direccion: dict[str, list[GeocodeCandidato]] | None = None) -> None:
        self.por_direccion = por_direccion or {}
        self.llamadas: list[str] = []

    async def geocode(self, direccion: str) -> list[GeocodeCandidato]:
        self.llamadas.append(direccion)
        return list(self.por_direccion.get(direccion, []))


class FakeGeocodeCacheRepository:
    def __init__(self) -> None:
        self.rows: dict[str, list[GeocodeCandidato]] = {}

    async def get(self, direccion_normalizada: str) -> list[GeocodeCandidato] | None:
        return self.rows.get(direccion_normalizada)

    async def put(
        self, direccion_normalizada: str, candidatos: list[GeocodeCandidato]
    ) -> None:
        self.rows[direccion_normalizada] = list(candidatos)


class FakeSucursalCoordenadasRepository:
    def __init__(self) -> None:
        self.rows: dict[int, SucursalCoordenadas] = {}

    async def list_by_prestador(self, prestador_id: UUID) -> list[SucursalCoordenadas]:
        return [r for r in self.rows.values() if r.prestador_id == prestador_id]

    async def get_by_siges_sucursal_id(
        self, siges_sucursal_id: int
    ) -> SucursalCoordenadas | None:
        return self.rows.get(siges_sucursal_id)

    async def upsert_pendiente(
        self,
        *,
        prestador_id: UUID,
        siges_sucursal_id: int,
        empresa_nombre: str,
        sucursal_nombre: str,
        direccion_normalizada: str | None,
    ) -> SucursalCoordenadas:
        existente = self.rows.get(siges_sucursal_id)
        if existente is not None:
            actualizada = dataclasses.replace(
                existente,
                empresa_nombre=empresa_nombre,
                sucursal_nombre=sucursal_nombre,
                direccion_normalizada=direccion_normalizada,
            )
        else:
            actualizada = SucursalCoordenadas(
                id=uuid.uuid4(),
                prestador_id=prestador_id,
                siges_sucursal_id=siges_sucursal_id,
                empresa_nombre=empresa_nombre,
                sucursal_nombre=sucursal_nombre,
                direccion_normalizada=direccion_normalizada,
                latitud=None,
                longitud=None,
                procedencia=None,
                formatted_address=None,
                fecha_resolucion=None,
                created_at=_AHORA,
                updated_at=_AHORA,
            )
        self.rows[siges_sucursal_id] = actualizada
        return actualizada

    async def resolver(
        self,
        siges_sucursal_id: int,
        *,
        latitud: float,
        longitud: float,
        procedencia: str,
        formatted_address: str | None,
    ) -> SucursalCoordenadas | None:
        existente = self.rows.get(siges_sucursal_id)
        if existente is None:
            return None
        resuelta = dataclasses.replace(
            existente,
            latitud=latitud,
            longitud=longitud,
            procedencia=procedencia,
            formatted_address=formatted_address,
            fecha_resolucion=_AHORA,
        )
        self.rows[siges_sucursal_id] = resuelta
        return resuelta


class FakeMatchingDescarteRepository:
    def __init__(self) -> None:
        self.rows: dict[UUID, set[int]] = {}

    async def create(self, tabla_km_id: UUID, siges_sucursal_id: int, usuario_email: str) -> None:
        self.rows.setdefault(tabla_km_id, set()).add(siges_sucursal_id)

    async def list_descartados_por_fila(
        self, tabla_km_ids: list[UUID]
    ) -> dict[UUID, set[int]]:
        return {tid: set(self.rows[tid]) for tid in tabla_km_ids if tid in self.rows}


class FakeIncidentesActividad:
    """Solo lo que usan los use cases geo del puerto de incidentes: el set de
    empresas con actividad reciente (ex-clientes = las que no están)."""

    def __init__(self, empresas: set[str] | None = None) -> None:
        self.empresas = empresas or set()

    async def empresas_con_actividad_reciente(
        self, prestador_id: UUID, desde_periodo: str
    ) -> set[str]:
        return set(self.empresas)


class FakeCalculoKmPreviewRepository:
    def __init__(self) -> None:
        self.rows: dict[UUID, CalculoKmPreview] = {}

    async def create(
        self,
        *,
        prestador_id: UUID,
        filas: tuple[PreviewFila, ...],
        sin_ubicar: int,
        sin_ruta: int,
        elementos_google: int,
        sin_actividad: int = 0,
    ) -> CalculoKmPreview:
        self.rows = {
            pid: p for pid, p in self.rows.items() if p.prestador_id != prestador_id
        }
        row = CalculoKmPreview(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            filas=filas,
            sin_ubicar=sin_ubicar,
            sin_ruta=sin_ruta,
            elementos_google=elementos_google,
            sin_actividad=sin_actividad,
            created_at=_AHORA,
        )
        self.rows[row.id] = row
        return row

    async def get_by_id(self, preview_id: UUID) -> CalculoKmPreview | None:
        return self.rows.get(preview_id)

    async def delete(self, preview_id: UUID) -> bool:
        return self.rows.pop(preview_id, None) is not None


class FakeGoogleMapsIdaVuelta:
    """Distancias configurables por destino; registra los lotes pedidos."""

    def __init__(
        self, tramos: dict[tuple[float, float], tuple[float | None, float | None]]
    ) -> None:
        self.tramos = tramos
        self.lotes: list[list[tuple[float, float]]] = []

    async def distancias_km(
        self,
        origin: tuple[float, float],
        destinations: list[tuple[float, float]],
    ) -> list[float | None]:
        return [self.tramos.get(d, (None, None))[0] for d in destinations]

    async def distancias_km_ida_vuelta(
        self,
        base: tuple[float, float],
        destinos: list[tuple[float, float]],
    ) -> list[tuple[float | None, float | None]]:
        self.lotes.append(list(destinos))
        return [self.tramos.get(d, (None, None)) for d in destinos]


class FakeCuadriculaBaseMapRepository:
    """Sin mapeos por defecto; tests de multi-base pueden añadir entradas directamente."""

    def __init__(self) -> None:
        self.rows: dict[tuple[UUID, str], CuadriculaBaseMap] = {}

    async def list_by_prestador(self, prestador_id: UUID) -> list[CuadriculaBaseMap]:
        return [v for k, v in self.rows.items() if k[0] == prestador_id]

    async def upsert(
        self, *, prestador_id: UUID, cuadricula: str, siges_base_sucursal_id: int
    ) -> CuadriculaBaseMap:
        entry = CuadriculaBaseMap(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            cuadricula=cuadricula,
            siges_base_sucursal_id=siges_base_sucursal_id,
            created_at=_AHORA,
        )
        self.rows[(prestador_id, cuadricula)] = entry
        return entry

    async def delete(self, *, prestador_id: UUID, cuadricula: str) -> None:
        self.rows.pop((prestador_id, cuadricula), None)


class FakeTablaKmGeoRepository:
    """Fake del puerto TablaKmRepository con los métodos de geolocalización."""

    def __init__(self, rows: list[TablaKm] | None = None) -> None:
        self.rows: dict[UUID, TablaKm] = {r.id: r for r in (rows or [])}

    async def get_by_id(self, tabla_km_id: UUID) -> TablaKm | None:
        return self.rows.get(tabla_km_id)

    async def list_by_prestador(self, prestador_id: UUID) -> list[TablaKm]:
        return [t for t in self.rows.values() if t.prestador_id == prestador_id]

    async def create(self, **kwargs: object) -> TablaKm:
        row = TablaKm(
            id=uuid.uuid4(),
            created_at=_AHORA,
            updated_at=_AHORA,
            **kwargs,  # type: ignore[arg-type]
        )
        self.rows[row.id] = row
        return row

    async def set_coordenadas(
        self,
        tabla_km_id: UUID,
        *,
        latitud: float,
        longitud: float,
        coords_origen: str,
        geocode_formatted_address: str | None,
        geocode_fecha: datetime | None,
    ) -> TablaKm | None:
        row = self.rows.get(tabla_km_id)
        if row is None:
            return None
        actualizada = dataclasses.replace(
            row,
            latitud_destino=latitud,
            longitud_destino=longitud,
            coords_origen=coords_origen,
            geocode_formatted_address=geocode_formatted_address,
            geocode_fecha=geocode_fecha,
        )
        self.rows[tabla_km_id] = actualizada
        return actualizada

    async def update_distancias(
        self,
        tabla_km_id: UUID,
        *,
        kms_ida: float,
        kms_vuelta: float,
        kms_recorrido: float,
        aplica_viatico: bool,
        kms_a_facturar: float,
        url_maps: str | None,
        latitud_destino: float,
        longitud_destino: float,
        coords_origen: str,
        siges_sucursal_id: int | None = None,
        id_costo_servicios: int | None = None,
    ) -> TablaKm | None:
        row = self.rows.get(tabla_km_id)
        if row is None:
            return None
        actualizada = dataclasses.replace(
            row,
            kms_ida=kms_ida,
            kms_vuelta=kms_vuelta,
            kms_recorrido=kms_recorrido,
            aplica_viatico=aplica_viatico,
            kms_a_facturar=kms_a_facturar,
            url_maps=url_maps,
            latitud_destino=latitud_destino,
            longitud_destino=longitud_destino,
            coords_origen=coords_origen,
            siges_sucursal_id=siges_sucursal_id if siges_sucursal_id is not None
            else row.siges_sucursal_id,
            id_costo_servicios=id_costo_servicios if id_costo_servicios is not None
            else row.id_costo_servicios,
        )
        self.rows[tabla_km_id] = actualizada
        return actualizada

    async def update_vinculo_siges(
        self,
        tabla_km_id: UUID,
        *,
        siges_sucursal_id: int,
        id_costo_servicios: int | None,
    ) -> TablaKm | None:
        row = self.rows.get(tabla_km_id)
        if row is None:
            return None
        actualizada = dataclasses.replace(
            row,
            siges_sucursal_id=siges_sucursal_id,
            id_costo_servicios=id_costo_servicios,
        )
        self.rows[tabla_km_id] = actualizada
        return actualizada

    async def update_domicilio(
        self,
        tabla_km_id: UUID,
        *,
        domicilio_cliente: str | None,
        localidad_cliente: str | None,
        provincia_cliente: str | None,
        siges_sucursal_id: int | None = None,
        id_costo_servicios: int | None = None,
    ) -> TablaKm | None:
        row = self.rows.get(tabla_km_id)
        if row is None:
            return None
        actualizada = dataclasses.replace(
            row,
            domicilio_cliente=domicilio_cliente,
            localidad_cliente=localidad_cliente,
            provincia_cliente=provincia_cliente,
            geocode_formatted_address=None,
            geocode_fecha=None,
            siges_sucursal_id=siges_sucursal_id if siges_sucursal_id is not None
            else row.siges_sucursal_id,
            id_costo_servicios=id_costo_servicios if id_costo_servicios is not None
            else row.id_costo_servicios,
        )
        self.rows[tabla_km_id] = actualizada
        return actualizada
