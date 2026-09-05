"""Piezas compartidas del cálculo de distancias y la geocodificación:
validación de prestador, coords de la base de despacho, parseo de lat/lon de
Siges (varchar con coma decimal), URL de Maps del viaje completo y control del
tope de llamadas a Google (la key es corporativa y paga)."""

from dataclasses import dataclass
from datetime import date
from urllib.parse import quote
from uuid import UUID

from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.errors import (
    BaseSucursalSinCoordenadasError,
    PrestadorNoEncontradoError,
    PrestadorSinBaseSucursalError,
    PrestadorSinVinculoSigesError,
    TopeLlamadasGoogleError,
)
from src.modules.liquidaciones.domain.repositories.calculo_km_preview_repository import (
    CalculoKmPreviewRepository,
)
from src.modules.liquidaciones.domain.repositories.google_maps_gateway import GoogleMapsGateway
from src.modules.liquidaciones.domain.repositories.incidente_repository import IncidenteRepository
from src.modules.liquidaciones.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
    SigesSucursalCliente,
    SigesSucursalPropia,
)
from src.modules.liquidaciones.domain.repositories.spst_repository import SpstRepository
from src.modules.liquidaciones.domain.repositories.sucursal_coordenadas_repository import (
    SucursalCoordenadasRepository,
)
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository
from src.modules.liquidaciones.domain.services.geolocalizacion import armar_direccion
from src.modules.liquidaciones.domain.services.vinculacion_siges import (
    nombres_compatibles,
    normalizar_nombre,
)

_MAPS_BASE = "https://www.google.com/maps/dir/?api=1"


@dataclass(frozen=True)
class CalcularDistanciasPorts:
    """Compartido por `PreviewCalcularDistancias` y `AplicarCalcularDistancias`
    (preview_calcular_distancias.py / aplicar_calcular_distancias.py)."""

    prestadores: PrestadorRepository
    tabla_km: TablaKmRepository
    siges: SigesCatalogoGateway
    google_maps: GoogleMapsGateway
    sucursal_coords: SucursalCoordenadasRepository
    previews: CalculoKmPreviewRepository
    incidentes: IncidenteRepository
    # Solo lo usa AplicarCalcularDistancias, para vincular SPST a las filas que
    # crea — ver ese archivo.
    spsts: SpstRepository


def es_empresa_activa(empresa_nombre: str, activos_norm: set[str]) -> bool:
    """Actividad reciente por nombre normalizado, tolerando variantes compatibles.
    Mismo criterio en Geocodificar, Distancias y Buscar sucursales (ex-clientes
    = las que no están en el set)."""
    empresa = normalizar_nombre(empresa_nombre)
    return empresa in activos_norm or any(
        nombres_compatibles(empresa, a) for a in activos_norm
    )


def desde_periodo_hace_meses(meses: int) -> str:
    hoy = date.today()
    mes = hoy.month - (meses % 12)
    anio = hoy.year - (meses // 12)
    if mes <= 0:
        mes += 12
        anio -= 1
    return f"{anio:04d}-{mes:02d}"


@dataclass(frozen=True)
class Destino:
    sucursal: SigesSucursalCliente
    coords: tuple[float, float]
    coords_origen: str


def parse_latlon_siges(lat: str | None, lon: str | None) -> tuple[float, float] | None:
    if lat is None or lon is None:
        return None
    try:
        parsed = float(lat.replace(",", ".")), float(lon.replace(",", "."))
    except ValueError:
        return None
    return None if parsed == (0.0, 0.0) else parsed


def maps_url_ida_vuelta(
    base: tuple[float, float],
    dest: tuple[float, float],
    *,
    domicilio: str | None = None,
    localidad: str | None = None,
    provincia: str | None = None,
) -> str:
    """Viaje completo base→cliente→base. Cuando hay dirección de texto usa el
    formato /maps/dir/ con la dirección como waypoint — Google la geocodifica
    y muestra el lugar correcto aunque el pin de Siges esté desplazado."""
    base_str = f"{base[0]},{base[1]}"
    direccion = armar_direccion(domicilio, localidad, provincia)
    if direccion:
        return f"https://www.google.com/maps/dir/{base_str}/{quote(direccion)}/{base_str}"
    return (
        f"{_MAPS_BASE}"
        f"&origin={base[0]},{base[1]}"
        f"&destination={base[0]},{base[1]}"
        f"&waypoints={dest[0]},{dest[1]}"
        f"&travelmode=driving"
    )


async def validar_prestador_vinculado_siges(
    prestadores: PrestadorRepository, prestador_id: UUID
) -> Prestador:
    prestador = await prestadores.get_by_id(prestador_id)
    if prestador is None:
        raise PrestadorNoEncontradoError(prestador_id)
    if prestador.siges_empresa_id is None:
        raise PrestadorSinVinculoSigesError(prestador_id)
    return prestador


async def validar_prestador_para_distancias(
    prestadores: PrestadorRepository, prestador_id: UUID
) -> Prestador:
    prestador = await validar_prestador_vinculado_siges(prestadores, prestador_id)
    if prestador.siges_base_sucursal_id is None:
        raise PrestadorSinBaseSucursalError(prestador_id)
    return prestador


def coords_base_default(
    prestador: Prestador, propias: list[SigesSucursalPropia]
) -> tuple[float, float]:
    base = next(
        (s for s in propias if s.siges_sucursal_id == prestador.siges_base_sucursal_id), None
    )
    if base is None:
        raise PrestadorSinBaseSucursalError(prestador.id)
    coords = parse_latlon_siges(base.latitud, base.longitud)
    if coords is None:
        raise BaseSucursalSinCoordenadasError(prestador.siges_base_sucursal_id)  # type: ignore[arg-type]
    return coords


def build_costo_bases(
    propias: list[SigesSucursalPropia],
) -> dict[int, tuple[float, float]]:
    resultado: dict[int, tuple[float, float]] = {}
    for s in propias:
        if s.id_costo_servicios is None:
            continue
        coords = parse_latlon_siges(s.latitud, s.longitud)
        if coords is not None:
            resultado[s.id_costo_servicios] = coords
    return resultado


async def obtener_coords_base(
    siges: SigesCatalogoGateway, prestador: Prestador
) -> tuple[float, float]:
    propias = await siges.list_sucursales_de_empresa(prestador.siges_empresa_id)  # type: ignore[arg-type]
    return coords_base_default(prestador, propias)


def verificar_tope(necesarias: int, tope: int) -> None:
    if necesarias > tope:
        raise TopeLlamadasGoogleError(necesarias, tope)


def calcular_kms_a_facturar(kms_total: float, umbral_viatico: float) -> tuple[bool, float]:
    aplica = kms_total > umbral_viatico
    return aplica, kms_total if aplica else 0.0
