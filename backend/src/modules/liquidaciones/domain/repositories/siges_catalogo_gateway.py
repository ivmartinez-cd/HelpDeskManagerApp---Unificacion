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
    insumo del alta asistida de Tabla KM (ADR-014, dataset 3). Solo datos
    descriptivos: el km esperado no existe en Siges, es dato manual."""

    siges_sucursal_id: int
    empresa_nombre: str
    sucursal_nombre: str
    domicilio: str | None
    localidad: str | None
    provincia: str | None


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
