"""Adapter pyodbc del puerto ProcesoEstimacionPort — combos de selección del
Estimador de Contadores contra Siges/MERCURIO. Plomería pyodbc en el
`MercurioQueryRunner` compartido (ADR-018), misma cuenta que el resto de
`contadores` (`SiGesReadOnly`, solo lectura)."""

from src.modules.contadores.domain.ports.proceso_estimacion_port import (
    AnexoOption,
    GrupoEconomicoOption,
    ProcesoOption,
)
from src.modules.contadores.infrastructure.siges.proceso_estimacion_query import (
    ANEXOS_POR_GRUPO_ECONOMICO_SQL,
    GRUPOS_ECONOMICOS_ACTIVOS_SQL,
    PROCESOS_POR_GRUPO_ECONOMICO_SQL,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner

_GATEWAY = "proceso_estimacion"


class PyodbcProcesoEstimacionGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def list_grupos_economicos_activos(self) -> list[GrupoEconomicoOption]:
        rows = await self._runner.fetch_all(
            GRUPOS_ECONOMICOS_ACTIVOS_SQL,
            gateway=_GATEWAY,
            log_message="Fallo el catálogo de grupos económicos activos contra Siges/MERCURIO",
        )
        return [GrupoEconomicoOption(id=int(r.id), descripcion=str(r.descripcion)) for r in rows]

    async def list_procesos_por_grupo(self, id_grupo_economico: int) -> list[ProcesoOption]:
        rows = await self._runner.fetch_all(
            PROCESOS_POR_GRUPO_ECONOMICO_SQL,
            [id_grupo_economico],
            gateway=_GATEWAY,
            log_message="Fallo la lista de procesos del grupo económico contra Siges/MERCURIO",
            log_extra={"id_grupo_economico": id_grupo_economico},
        )
        return [
            ProcesoOption(
                nro_proceso=int(r.Nro_Proceso),
                periodo_facturacion=str(r.PeriodoFacturacion),
                nombre_anexo=str(r.NombreAnexo),
                periodo_hasta=r.PeriodoHasta,
                id_anexo=int(r.ID_Anexo),
            )
            for r in rows
        ]

    async def list_anexos_por_grupo(self, id_grupo_economico: int) -> list[AnexoOption]:
        rows = await self._runner.fetch_all(
            ANEXOS_POR_GRUPO_ECONOMICO_SQL,
            [id_grupo_economico],
            gateway=_GATEWAY,
            log_message="Fallo la lista de anexos del grupo económico contra Siges/MERCURIO",
            log_extra={"id_grupo_economico": id_grupo_economico},
        )
        return [
            AnexoOption(id_anexo=int(r.ID_Anexo), nombre_anexo=str(r.NombreAnexo)) for r in rows
        ]
