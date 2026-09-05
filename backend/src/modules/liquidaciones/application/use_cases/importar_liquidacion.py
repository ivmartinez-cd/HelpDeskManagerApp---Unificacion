"""Caso de uso ImportarLiquidacion — port de POST /liquidaciones/importar.

`total_importe` se calcula acá mismo (ya se conoce del parseo, sin round-trip a la
DB) en vez del segundo `UPDATE` que hacía el legacy después de insertar los
incidentes — mismo valor final, un paso menos. El análisis (motor de reglas +
persistencia de alertas/observaciones/enriquecimiento) se delega en
`ReanalizarLiquidacion` en vez de duplicarlo: es exactamente la misma lógica que
corría `ejecutar_motor` al final del import en el legacy.
"""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.dtos.importar_liquidacion import (
    ImportarLiquidacionResultado,
)
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
)
from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
from src.modules.liquidaciones.domain.errors import PrestadorNoEncontradoError
from src.modules.liquidaciones.domain.repositories.incidente_repository import (
    IncidenteRepository,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_file_parser import (
    LiquidacionFileParser,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    ResultadoImportacion,
)


@dataclass(frozen=True)
class ImportarLiquidacionPorts:
    parser: LiquidacionFileParser
    prestadores: PrestadorRepository
    liquidaciones: LiquidacionRepository
    incidentes: IncidenteRepository
    reanalizar: ReanalizarLiquidacion


class ImportarLiquidacion:
    def __init__(self, ports: ImportarLiquidacionPorts) -> None:
        self._ports = ports

    async def execute(
        self, *, prestador_id: UUID, contenido: bytes, nombre_archivo: str
    ) -> ImportarLiquidacionResultado:
        if await self._ports.prestadores.get_by_id(prestador_id) is None:
            raise PrestadorNoEncontradoError(prestador_id)

        resultado_parseo = self._ports.parser.parse(contenido, nombre_archivo)
        liquidacion = await self._crear_liquidacion(prestador_id, nombre_archivo, resultado_parseo)
        await self._ports.incidentes.bulk_create(liquidacion.id, resultado_parseo.incidentes)
        analisis = await self._ports.reanalizar.execute(liquidacion.id)

        return ImportarLiquidacionResultado(
            liquidacion_id=liquidacion.id,
            total_incidentes=analisis.total_incidentes,
            total_alertas=analisis.total_alertas,
        )

    async def _crear_liquidacion(
        self, prestador_id: UUID, nombre_archivo: str, resultado_parseo: ResultadoImportacion
    ) -> Liquidacion:
        total_importe = round(sum(i.costo_total_cobrado for i in resultado_parseo.incidentes), 2)
        return await self._ports.liquidaciones.create(
            prestador_id=prestador_id,
            numero_liquidacion=resultado_parseo.numero_liquidacion,
            periodo=resultado_parseo.periodo,
            tipo_liquidacion=resultado_parseo.tipo_liquidacion,
            nombre_archivo=nombre_archivo,
            total_incidentes=len(resultado_parseo.incidentes),
            total_importe=total_importe,
        )
