"""Caso de uso SincronizarLiquidaciones — importa desde el SOAP de Canal Directo
las liquidaciones nuevas que todavía no están en la DB.

Solo procesa prestadores con `cd_prestador_id` configurado; los demás se
contabilizan en `sin_prestador` y se ignoran (nunca lanzan error).
"""

import logging
from dataclasses import dataclass

from src.modules.liquidaciones.application.dtos.sincronizar_liquidaciones import (
    SincronizarLiquidacionesResultado,
)
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
)
from src.modules.liquidaciones.domain.entities.liquidacion import TIPO_REGULAR
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.repositories.cd_liquidaciones_gateway import (
    CdLiquidacionesGateway,
)
from src.modules.liquidaciones.domain.repositories.incidente_repository import (
    IncidenteRepository,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)
from src.modules.liquidaciones.domain.services.importacion.metadata import extraer_periodo
from src.modules.liquidaciones.domain.services.importacion.normalizacion import (
    normalizar_tipo_servicio,
)
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import (
    CdIncidenteRow,
    CdLiquidacion,
)
from src.modules.liquidaciones.domain.value_objects.incidente_importado import IncidenteImportado

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SincronizarLiquidacionesPorts:
    cd_gateway: CdLiquidacionesGateway
    prestadores: PrestadorRepository
    liquidaciones: LiquidacionRepository
    incidentes: IncidenteRepository
    reanalizar: ReanalizarLiquidacion


class SincronizarLiquidaciones:
    def __init__(self, ports: SincronizarLiquidacionesPorts) -> None:
        self._ports = ports

    async def execute(self) -> SincronizarLiquidacionesResultado:
        prestadores_cd = await self._ports.prestadores.list_con_cd_id()
        existentes = await self._ports.liquidaciones.list_numeros_liquidacion()
        creadas, ya_existentes = 0, 0
        for prestador in prestadores_cd:
            assert prestador.cd_prestador_id is not None
            liqs = await self._ports.cd_gateway.get_liquidaciones(prestador.cd_prestador_id)
            for cd_liq in liqs:
                if cd_liq.numero_liquidacion in existentes:
                    ya_existentes += 1
                else:
                    await self._procesar(cd_liq, prestador)
                    existentes.add(cd_liq.numero_liquidacion)
                    creadas += 1
        return SincronizarLiquidacionesResultado(
            creadas=creadas,
            ya_existentes=ya_existentes,
            sin_prestador=0,
        )

    async def _procesar(self, cd_liq: CdLiquidacion, prestador: Prestador) -> None:
        filas_cd = await self._ports.cd_gateway.get_incidentes(cd_liq.id)
        incidentes = [_a_importado(r) for r in filas_cd]
        periodo = extraer_periodo("", incidentes) or _periodo_desde_fecha(cd_liq)
        total = round(sum(i.costo_total_cobrado for i in incidentes), 2)
        liq = await self._ports.liquidaciones.create(
            prestador_id=prestador.id,
            numero_liquidacion=cd_liq.numero_liquidacion,
            periodo=periodo,
            tipo_liquidacion=TIPO_REGULAR,
            nombre_archivo=None,
            total_incidentes=len(incidentes),
            total_importe=total,
        )
        await self._ports.incidentes.bulk_create(liq.id, incidentes)
        await self._ports.reanalizar.execute(liq.id)


def _a_importado(row: CdIncidenteRow) -> IncidenteImportado:
    total_viaje = round(row.cant_km * row.costo_km, 2)
    return IncidenteImportado(
        numero_incidente=str(row.id),
        rubro=row.rubro or "Impresoras",
        tipo=normalizar_tipo_servicio(row.tipo),
        empresa_nombre=row.empresa_nombre,
        sucursal_nombre=row.sucursal_nombre,
        nro_serie=row.nro_serie,
        fecha_cierre=row.fecha_cierre,
        costo_servicio_cobrado=row.costo_servicio,
        cant_km_cobrado=row.cant_km,
        costo_km_cobrado=row.costo_km,
        total_viaje_cobrado=total_viaje,
        costo_total_cobrado=round(row.costo_servicio + total_viaje, 2),
        pasa_it=row.pasa_it,
    )


def _periodo_desde_fecha(cd_liq: CdLiquidacion) -> str:
    f = cd_liq.fecha_liquidacion
    if f.month == 1:
        return f"{f.year - 1}-12"
    return f"{f.year}-{f.month - 1:02d}"
