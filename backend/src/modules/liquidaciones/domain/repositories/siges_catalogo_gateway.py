"""Puerto de lectura del catálogo de PST/SPST en Siges (`dbo.Empresa`, ADR-014).

Solo lectura por diseño: la cuenta `SiGesReadOnly` no tiene permisos de escritura,
y este puerto no expone ninguna operación que la necesite.
"""

from dataclasses import dataclass
from typing import Literal, Protocol

TipoEmpresaSiges = Literal["PST", "SPST"]


@dataclass(frozen=True)
class SigesEmpresaInfo:
    siges_empresa_id: int
    den_comercial: str
    razon_social: str | None
    cuit: str | None
    tipo: TipoEmpresaSiges


class SigesCatalogoGateway(Protocol):
    async def list_empresas_activas(self) -> list[SigesEmpresaInfo]:
        """Empresas activas (`Estado=0` — semántica invertida verificada en el
        ADR-014) cuyo `Den_Comercial` empieza con `'PST '` o `'SPST'`."""
        ...
