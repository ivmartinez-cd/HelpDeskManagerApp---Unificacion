"""Adapter pyodbc del puerto DespachosSigesGateway. La plomería (thread, timeouts,
`pyodbc.Error` -> `ExternalServiceError` con log) vive en el `OrionQueryRunner`
compartido (ADR-018); acá quedan los parámetros de la consulta y la validación de la
entrada. El log de error lleva la ventana y las distribuciones en el propio mensaje porque
el formateador JSON del repo descarta `extra`.
"""

from src.modules.insumos.domain.value_objects.despachados.despacho_siges import DespachoSiges
from src.modules.insumos.infrastructure.siges.consulta_despachos import (
    construir_consulta_despachos,
)
from src.modules.insumos.infrastructure.siges.mapeo_despachos import mapear_despachos
from src.shared.infrastructure.orion.query_runner import OrionQueryRunner


class PyodbcDespachosSigesGateway:
    def __init__(self, runner: OrionQueryRunner) -> None:
        self._runner = runner

    async def listar_despachos_oca(
        self, *, dias_ventana: int, distribuciones: tuple[int, ...]
    ) -> list[DespachoSiges]:
        if dias_ventana < 1:
            raise ValueError(f"dias_ventana tiene que ser al menos 1 (llegó {dias_ventana})")
        if not distribuciones:
            return []
        contexto = f"dias_ventana={dias_ventana}, distribuciones={list(distribuciones)}"
        filas = await self._runner.fetch_all(
            construir_consulta_despachos(len(distribuciones)),
            (*distribuciones, dias_ventana),
            gateway="insumos_despachados_siges",
            log_message=f"Falló la consulta de despachos OCA contra Siges/ORION ({contexto})",
            log_extra={"dias_ventana": dias_ventana, "distribuciones": list(distribuciones)},
        )
        return mapear_despachos(filas)
