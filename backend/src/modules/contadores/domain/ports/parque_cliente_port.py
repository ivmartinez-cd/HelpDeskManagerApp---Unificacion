from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class EmpresaSiges:
    """Una empresa activa del catálogo de Siges (`dbo.Empresa`, `Estado=0`) —
    lo mínimo para cruzar por nombre el `cliente` de los eventos de Gestión."""

    id: int
    den_comercial: str


@dataclass(frozen=True, slots=True)
class EmpresaConParque:
    """Resultado de búsqueda para resolver un cliente sin cruce: la empresa
    con su parque activo, para elegir con información a la vista."""

    id: int
    den_comercial: str
    impresoras: int


class ParqueClientePort(Protocol):
    """Puerto de solo lectura contra Siges para el parque de impresoras por
    cliente. Misma cuenta `db_datareader` y misma definición de "máquina
    activa" que el parque por PST (ver SIGES_READONLY_CATALOGO_DATOS.md §3)."""

    async def list_empresas_activas(self) -> list[EmpresaSiges]: ...

    async def count_impresoras_by_empresa_ids(self, empresa_ids: list[int]) -> dict[int, int]:
        """Impresoras activas por `ID_Empresa`. Una empresa sin máquinas puede
        no aparecer en el dict: tratar ausencia como 0."""
        ...

    async def search_empresas_activas(self, texto: str) -> list[EmpresaConParque]:
        """Empresas activas cuyo nombre contiene `texto`, con su parque —
        para el modal que resuelve clientes sin cruce."""
        ...
