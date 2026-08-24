"""Adapter pyodbc del puerto SigesTecnicoGateway. La plomería pyodbc vive en
el `MercurioQueryRunner` compartido (ADR-018); acá quedan el SQL y el mapeo de
filas propios del catálogo de técnicos de vacaciones."""

from src.modules.vacaciones.domain.services.vinculacion_siges import SigesTecnicoInfo
from src.modules.vacaciones.infrastructure.siges.query import TECNICOS_ACTIVOS_SQL
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcSigesTecnicoGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def list_tecnicos_activos(self) -> list[SigesTecnicoInfo]:
        rows = await self._runner.fetch_all(
            TECNICOS_ACTIVOS_SQL,
            gateway="vacaciones_siges",
            log_message="Fallo la consulta del catálogo de técnicos contra Siges/MERCURIO",
        )
        return [
            SigesTecnicoInfo(
                siges_empresa_id=int(row.ID_Empresa),
                den_comercial=str(row.Den_Comercial).strip(),
            )
            for row in rows
        ]
