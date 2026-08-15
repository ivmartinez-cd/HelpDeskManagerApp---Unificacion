"""Caso de uso SincronizarLiquidaciones — importa desde el SOAP de Canal Directo
las liquidaciones nuevas que todavía no están en la DB.

Solo procesa prestadores activos con `cd_prestador_id` configurado; los activos
sin vínculo se contabilizan en `sin_prestador` y se ignoran (nunca lanzan error).
Si el detalle SOAP de una liquidación falla o vuelve vacío cuando el listado
declaraba incidentes, la liquidación NO se crea y se cuenta en `fallidas` — el
sync es aditivo puro, así que una liquidación creada vacía por un fallo
transitorio quedaría vacía para siempre (hallazgo H-2 de la validación
2026-08-13); al no crearla, la corrida siguiente la reintenta.
"""

import logging
from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.dtos.sincronizar_liquidaciones import (
    SincronizarLiquidacionesResultado,
)
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
)
from src.modules.liquidaciones.domain.entities.liquidacion import (
    ESTADO_ABIERTA,
    ESTADO_OBSERVADA,
    ESTADO_PRELIQUIDADA,
    ESTADO_RECIBIDA,
    TIPO_REGULAR,
)
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

# Estados que pueden ser anulados en AyC mientras siguen abiertos localmente.
# Las terminales (aprobada, cerrada) no se tocan — no se anulan en AyC después de cerradas.
_ESTADOS_PENDIENTES = frozenset(
    {ESTADO_ABIERTA, ESTADO_PRELIQUIDADA, ESTADO_RECIBIDA, ESTADO_OBSERVADA}
)

# Nombres de estado que AyC puede devolver para una liquidación anulada, en caso de que
# getTopLiquidations las incluya con estado explícito en lugar de omitirlas.
_ESTADOS_CD_ANULADOS = frozenset({"anulada", "anulado", "cancelada", "void", "voided"})


@dataclass(frozen=True)
class SincronizarLiquidacionesPorts:
    cd_gateway: CdLiquidacionesGateway
    prestadores: PrestadorRepository
    liquidaciones: LiquidacionRepository
    incidentes: IncidenteRepository
    reanalizar: ReanalizarLiquidacion


@dataclass
class _Contadores:
    creadas: int = 0
    ya_existentes: int = 0
    fallidas: int = 0
    anuladas: int = 0


class SincronizarLiquidaciones:
    def __init__(self, ports: SincronizarLiquidacionesPorts) -> None:
        self._ports = ports

    async def execute(
        self, prestador_id: UUID | None = None
    ) -> SincronizarLiquidacionesResultado:
        """`prestador_id` acota el sync a un solo prestador (debe estar vinculado);
        con None sincroniza todos los vinculados."""
        prestadores_cd = await self._ports.prestadores.list_con_cd_id()
        if prestador_id is not None:
            prestadores_cd = [p for p in prestadores_cd if p.id == prestador_id]
        activos = await self._ports.prestadores.list_all(solo_activos=True)
        sin_prestador = sum(1 for p in activos if p.cd_prestador_id is None)

        existentes = await self._ports.liquidaciones.list_numeros_liquidacion()
        totales = _Contadores()
        for prestador in prestadores_cd:
            parciales = await self._sincronizar_prestador(prestador, existentes)
            logger.info(
                "sync CD %s: %d creadas, %d ya existentes, %d fallidas",
                prestador.nombre_corto,
                parciales.creadas,
                parciales.ya_existentes,
                parciales.fallidas,
            )
            totales.creadas += parciales.creadas
            totales.ya_existentes += parciales.ya_existentes
            totales.fallidas += parciales.fallidas

        return SincronizarLiquidacionesResultado(
            creadas=totales.creadas,
            ya_existentes=totales.ya_existentes,
            sin_prestador=sin_prestador,
            fallidas=totales.fallidas,
            anuladas=totales.anuladas,
        )

    async def _sincronizar_prestador(
        self, prestador: Prestador, existentes: set[str]
    ) -> _Contadores:
        assert prestador.cd_prestador_id is not None
        contadores = _Contadores()
        liqs = await self._ports.cd_gateway.get_liquidaciones(prestador.cd_prestador_id)
        for cd_liq in liqs:
            if cd_liq.numero_liquidacion in existentes:
                contadores.ya_existentes += 1
            elif await self._procesar(cd_liq, prestador):
                existentes.add(cd_liq.numero_liquidacion)
                contadores.creadas += 1
            else:
                contadores.fallidas += 1
        contadores.anuladas = await self._detectar_y_eliminar_anuladas(liqs, prestador)
        return contadores

    async def _detectar_y_eliminar_anuladas(
        self, liqs: list[CdLiquidacion], prestador: Prestador
    ) -> int:
        """Elimina localmente las liquidaciones pendientes que AyC ya no reporta como vigentes.

        No hace llamadas SOAP extra: reutiliza `liqs` ya obtenida por `_sincronizar_prestador`.
        Guarda contra SOAP vacío: si `liqs` está vacío (fallo de red u otro error),
        no toca nada — evita eliminar falsamente todo el historial local del prestador.

        Detecta dos comportamientos posibles de AyC:
        - Que omita las anuladas del response (la más común): ausencia en `liqs`.
        - Que las incluya con un estado explícito (ej. "Anulada"): campo `estado`.
        """
        if not liqs:
            return 0

        cd_vigentes = {
            cd_liq.numero_liquidacion
            for cd_liq in liqs
            if cd_liq.estado.lower() not in _ESTADOS_CD_ANULADOS
        }
        # Límite superior del window: el ID numérico más alto retornado por AyC.
        # Solo se eliminan locales con ID ≤ ese máximo para no tocar liquidaciones
        # más viejas que el top-N del SOAP (que podrían estar fuera del window).
        max_cd_id = max(cd_liq.id for cd_liq in liqs)

        locales = await self._ports.liquidaciones.list_activas_por_prestador_con_numero(
            prestador.id, _ESTADOS_PENDIENTES
        )
        eliminadas = 0
        for liq in locales:
            assert liq.numero_liquidacion is not None
            try:
                local_ayc_id = int(liq.numero_liquidacion.split("-")[0])
            except (ValueError, IndexError):
                continue
            if local_ayc_id <= max_cd_id and liq.numero_liquidacion not in cd_vigentes:
                await self._ports.liquidaciones.delete(liq.id)
                eliminadas += 1
                logger.info(
                    "sync CD %s: liquidación %s eliminada localmente (no vigente en AyC)",
                    prestador.nombre_corto,
                    liq.numero_liquidacion,
                )
        return eliminadas

    async def _procesar(self, cd_liq: CdLiquidacion, prestador: Prestador) -> bool:
        """Crea la liquidación con sus incidentes. False (sin crear) si el detalle
        SOAP no devolvió los incidentes que el listado declaraba."""
        filas_cd = await self._ports.cd_gateway.get_incidentes(cd_liq.id)
        if not filas_cd and cd_liq.cant_incidentes > 0:
            logger.warning(
                "sync CD: liquidación %s (%s) declara %d incidentes pero el detalle "
                "volvió vacío — no se crea, se reintenta en el próximo sync",
                cd_liq.numero_liquidacion,
                prestador.nombre_corto,
                cd_liq.cant_incidentes,
            )
            return False
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
        return True


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
