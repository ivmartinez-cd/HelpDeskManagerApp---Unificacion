"""Puerto de lectura del catálogo de PST/SPST y tarifarios en Siges (ADR-014).

Solo lectura por diseño: la cuenta `SiGesReadOnly` no tiene permisos de escritura,
y este puerto no expone ninguna operación que la necesite.
"""

from dataclasses import dataclass
from datetime import date
from typing import Literal, Protocol

TipoEmpresaSiges = Literal["PST", "SPST"]


@dataclass(frozen=True)
class SigesEmpresaInfo:
    siges_empresa_id: int
    den_comercial: str
    razon_social: str | None
    cuit: str | None
    tipo: TipoEmpresaSiges


@dataclass(frozen=True)
class SigesCostoServicio:
    """Fila wide de `dbo.CostoServicio`: una vigencia del tarifario de un PST,
    con un costo por tipo de servicio en columnas. Solo los 6 tipos con
    equivalente local — `inclusion_a_contrato`/`relevamiento`/`presupuesto`/
    `taller` se ignoran por decisión del ADR-014."""

    siges_empresa_id: int
    descripcion: str
    vigencia_desde: date
    costo_km: float
    correctivo: float
    preventivo: float
    instalacion: float
    pre_correctivo: float
    guardia: float
    sistemas: float


@dataclass(frozen=True)
class SigesSucursalCliente:
    """Sucursal de cliente asignada a un PST (`dbo.Sucursal.ID_Prestador`) —
    insumo del alta asistida y cálculo de distancias (ADR-014, dataset 3).

    `id_costo_servicios` coincide con el mismo campo de la sucursal propia del
    PST que la atiende — permite auto-seleccionar la base de origen correcta sin
    configuración manual (confirmado en PST 504 y INFOMAC, 2026-08-16)."""

    siges_sucursal_id: int
    empresa_nombre: str
    sucursal_nombre: str
    domicilio: str | None
    localidad: str | None
    provincia: str | None
    latitud: str | None = None
    longitud: str | None = None
    cuadricula: str | None = None
    id_costo_servicios: int | None = None


@dataclass(frozen=True)
class SigesSucursalPropia:
    """Sucursal de la propia empresa del PST (`dbo.Sucursal.Id_Empresa`) —
    insumo del selector de base de despacho y del auto-mapping por costo."""

    siges_sucursal_id: int
    descripcion: str
    latitud: str | None
    longitud: str | None
    id_costo_servicios: int | None = None


class SigesCatalogoGateway(Protocol):
    async def list_empresas_activas(self) -> list[SigesEmpresaInfo]:
        """Empresas activas (`Estado=0` — semántica invertida verificada en el
        ADR-014) cuyo `Den_Comercial` empieza con `'PST '` o `'SPST'`."""
        ...

    async def list_costos_habilitados(
        self, siges_empresa_ids: list[int]
    ) -> list[SigesCostoServicio]:
        """Vigencias de `CostoServicio` con `habilitado=1` de las empresas
        pedidas. Sin duplicados por (empresa, descripción, vigencia) — verificado
        con dato real 2026-08-13."""
        ...

    async def list_sucursales_de_prestador(
        self, siges_empresa_id: int
    ) -> list[SigesSucursalCliente]:
        """Sucursales de cliente activas (`Estado=0`) asignadas al PST."""
        ...

    async def list_sucursales_de_empresa(
        self, siges_empresa_id: int
    ) -> list[SigesSucursalPropia]:
        """Sucursales propias del PST (`Id_Empresa = siges_empresa_id`) —
        sus sedes/bases de despacho, con coordenadas."""
        ...

    async def list_cuadriculas_de_prestador(
        self, siges_empresa_id: int
    ) -> list[str]:
        """Cuadrículas distintas (Cod. Agrupación en Gestión) de las sucursales
        cliente activas asignadas al PST — vacíos y NULL excluidos."""
        ...
