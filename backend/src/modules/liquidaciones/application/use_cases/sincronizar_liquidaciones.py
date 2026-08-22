"""Caso de uso SincronizarLiquidaciones — importa desde el SOAP de Canal Directo
las liquidaciones que todavía no están en la DB, y reconcilia las que ya existen
(estado, costos/km de incidentes) contra lo que reporta AyC.

Solo procesa prestadores activos con `cd_prestador_id` configurado; los activos
sin vínculo se contabilizan en `sin_prestador` y se ignoran (nunca lanzan error).
Si el detalle SOAP de una liquidación falla, o vuelve con una cantidad de
incidentes distinta a la que el listado declaraba (vacío total o parcial), la
liquidación NO se crea y se cuenta en `fallidas` — el sync es aditivo puro para
las nuevas, así que una liquidación creada vacía o incompleta por un fallo
transitorio quedaría así para siempre (hallazgo H-2 de la validación
2026-08-13); al no crearla, la corrida siguiente la reintenta.

Las liquidaciones ya existentes y no terminales (`abierta`/`preliquidada`/
`recibida`/`observada`) se reconcilian vía `ReconciliarLiquidacion` — ver ese
módulo para el porqué de "actualizar in-place, nunca borrar y recrear". Las
`aprobada`/`cerrada` quedan congeladas, ni se les pide el detalle SOAP.
"""

import logging
from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.dtos.sincronizar_liquidaciones import (
    SincronizarLiquidacionesResultado,
)
from src.modules.liquidaciones.application.use_cases._cd_mapping import (
    a_importado,
    periodo_desde_fecha,
)
from src.modules.liquidaciones.application.use_cases._reconciliar_liquidacion import (
    ReconciliarLiquidacion,
    ReconciliarLiquidacionResultado,
)
from src.modules.liquidaciones.application.use_cases._sincronizar_contadores import Contadores
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
)
from src.modules.liquidaciones.domain.entities.liquidacion import (
    ESTADO_ABIERTA,
    ESTADO_OBSERVADA,
    ESTADO_PRELIQUIDADA,
    ESTADO_RECIBIDA,
    TIPO_REGULAR,
    Liquidacion,
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
from src.modules.liquidaciones.domain.services.detectar_anuladas import detectar_anuladas
from src.modules.liquidaciones.domain.services.importacion.metadata import extraer_periodo
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import (
    CdIncidenteRow,
    CdLiquidacion,
)
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)

# Estados que pueden ser anulados en AyC mientras siguen abiertos localmente.
# Las terminales (aprobada, cerrada) no se tocan — no se anulan en AyC después de cerradas.
_ESTADOS_PENDIENTES = frozenset(
    {ESTADO_ABIERTA, ESTADO_PRELIQUIDADA, ESTADO_RECIBIDA, ESTADO_OBSERVADA}
)


@dataclass(frozen=True)
class SincronizarLiquidacionesPorts:
    cd_gateway: CdLiquidacionesGateway
    prestadores: PrestadorRepository
    liquidaciones: LiquidacionRepository
    incidentes: IncidenteRepository
    reanalizar: ReanalizarLiquidacion
    reconciliar: ReconciliarLiquidacion


class SincronizarLiquidaciones:
    def __init__(self, ports: SincronizarLiquidacionesPorts) -> None:
        self._ports = ports

    async def execute(
        self, prestador_id: UUID | None = None, *, permitir_eliminar_anuladas: bool = True
    ) -> SincronizarLiquidacionesResultado:
        """`prestador_id` acota el sync a un solo prestador (debe estar vinculado);
        con None sincroniza todos los vinculados. `permitir_eliminar_anuladas=False`
        salta `_detectar_y_eliminar_anuladas` entero — la usa el job de fondo
        (`presentation/background_jobs.py`), que nunca borra sin que alguien esté
        mirando; el botón/endpoint manual la deja en `True`."""
        prestadores_cd, sin_prestador = await self._prestadores_a_sincronizar(prestador_id)
        existentes = await self._ports.liquidaciones.list_numeros_liquidacion()
        totales = Contadores()
        for prestador in prestadores_cd:
            parciales = await self._sincronizar_prestador(
                prestador, existentes, permitir_eliminar_anuladas=permitir_eliminar_anuladas
            )
            _log_parciales(prestador, parciales)
            totales.sumar(parciales)
        return totales.a_resultado(sin_prestador=sin_prestador)

    async def _prestadores_a_sincronizar(
        self, prestador_id: UUID | None
    ) -> tuple[list[Prestador], int]:
        """Prestadores vinculados a CD (acotados a `prestador_id` si viene) y la
        cantidad de activos sin vínculo, que quedan fuera del sync."""
        prestadores_cd = await self._ports.prestadores.list_con_cd_id()
        if prestador_id is not None:
            prestadores_cd = [p for p in prestadores_cd if p.id == prestador_id]
        activos = await self._ports.prestadores.list_all(solo_activos=True)
        sin_prestador = sum(1 for p in activos if p.cd_prestador_id is None)
        return prestadores_cd, sin_prestador

    async def _sincronizar_prestador(
        self, prestador: Prestador, existentes: set[str], *, permitir_eliminar_anuladas: bool
    ) -> Contadores:
        contadores = Contadores()
        liqs, pendientes, por_numero = await self._listados_remoto_y_local(prestador)
        for cd_liq in liqs:
            if cd_liq.numero_liquidacion in existentes:
                contadores.ya_existentes += 1
                contadores.registrar_reconciliacion(await self._reconciliar(cd_liq, por_numero))
            elif await self._procesar(cd_liq, prestador):
                existentes.add(cd_liq.numero_liquidacion)
                contadores.creadas += 1
            else:
                contadores.fallidas += 1
        if permitir_eliminar_anuladas:
            contadores.anuladas = await self._detectar_y_eliminar_anuladas(
                liqs, prestador, pendientes
            )
        return contadores

    async def _listados_remoto_y_local(
        self, prestador: Prestador
    ) -> tuple[list[CdLiquidacion], list[Liquidacion], dict[str | None, Liquidacion]]:
        """Los dos lados del cruce: lo que AyC reporta para el prestador, y las
        liquidaciones locales no terminales (lista, y la misma indexada por número)."""
        assert prestador.cd_prestador_id is not None
        liqs = await self._ports.cd_gateway.get_liquidaciones(prestador.cd_prestador_id)
        pendientes = await self._ports.liquidaciones.list_activas_por_prestador_con_numero(
            prestador.id, _ESTADOS_PENDIENTES
        )
        return liqs, pendientes, {liq.numero_liquidacion: liq for liq in pendientes}

    async def _reconciliar(
        self, cd_liq: CdLiquidacion, pendientes_por_numero: dict[str | None, Liquidacion]
    ) -> ReconciliarLiquidacionResultado | None:
        """None si la liquidación está en estado terminal (no está en
        `pendientes_por_numero`) o el detalle SOAP falló — en ambos casos no se
        intentó reconciliar. Si se intentó, el resultado indica si además hubo
        un guard interno de `ReconciliarLiquidacion` (mismatch de cantidad,
        bajas masivas) que abortó sin aplicar nada (`reconciliada=False`)."""
        liquidacion = pendientes_por_numero.get(cd_liq.numero_liquidacion)
        if liquidacion is None:
            return None
        filas_cd = await self._detalle_para_reconciliar(cd_liq)
        if filas_cd is None:
            return None
        remotos = [a_importado(r) for r in filas_cd]
        resultado = await self._ports.reconciliar.execute(liquidacion, cd_liq, remotos)
        _log_reconciliada(cd_liq, resultado)
        return resultado

    async def _detalle_para_reconciliar(
        self, cd_liq: CdLiquidacion
    ) -> list[CdIncidenteRow] | None:
        """Detalle SOAP de la liquidación, o None si falló (se reintenta en el
        próximo sync — la reconciliación no se intenta con datos parciales)."""
        try:
            return await self._ports.cd_gateway.get_incidentes(cd_liq.id)
        except ExternalServiceError:
            logger.warning(
                "sync CD: detalle SOAP falló al reconciliar %s — se reintenta en "
                "el próximo sync",
                cd_liq.numero_liquidacion,
            )
            return None

    async def _detectar_y_eliminar_anuladas(
        self, liqs: list[CdLiquidacion], prestador: Prestador, locales: list[Liquidacion]
    ) -> int:
        """Elimina localmente las liquidaciones pendientes que AyC ya no reporta como
        vigentes (`detectar_anuladas`, diff puro). No hace llamadas SOAP extra:
        reutiliza `liqs`/`locales` ya obtenidas por `_sincronizar_prestador`."""
        anuladas = detectar_anuladas(liqs, locales)
        for liq in anuladas:
            await self._ports.liquidaciones.delete(liq.id)
            logger.info(
                "sync CD %s: liquidación %s eliminada localmente (no vigente en AyC)",
                prestador.nombre_corto,
                liq.numero_liquidacion,
            )
        return len(anuladas)

    async def _procesar(self, cd_liq: CdLiquidacion, prestador: Prestador) -> bool:
        """Crea la liquidación con sus incidentes. False (sin crear) si el detalle
        SOAP falló o no devolvió la misma cantidad de incidentes que el listado
        declaraba (vacío total o parcial — ambos indican una respuesta incompleta)."""
        try:
            filas_cd = await self._ports.cd_gateway.get_incidentes(cd_liq.id)
        except ExternalServiceError:
            logger.warning(
                "sync CD: detalle SOAP falló para %s (%s) — no se crea, se reintenta "
                "en el próximo sync",
                cd_liq.numero_liquidacion,
                prestador.nombre_corto,
            )
            return False
        if len(filas_cd) != cd_liq.cant_incidentes:
            logger.warning(
                "sync CD: liquidación %s (%s) declara %d incidentes pero el detalle "
                "trajo %d — no se crea, se reintenta en el próximo sync",
                cd_liq.numero_liquidacion,
                prestador.nombre_corto,
                cd_liq.cant_incidentes,
                len(filas_cd),
            )
            return False
        incidentes = [a_importado(r) for r in filas_cd]
        periodo = extraer_periodo("", incidentes) or periodo_desde_fecha(cd_liq)
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


def _log_parciales(prestador: Prestador, parciales: Contadores) -> None:
    logger.info(
        "sync CD %s: %d creadas, %d ya existentes, %d fallidas, %d anuladas, "
        "%d reconciliadas, %d estados actualizados, %d extras actualizados, "
        "%d facturas actualizadas",
        prestador.nombre_corto,
        parciales.creadas,
        parciales.ya_existentes,
        parciales.fallidas,
        parciales.anuladas,
        parciales.reconciliadas,
        parciales.estados_actualizados,
        parciales.extras_actualizados,
        parciales.facturas_actualizadas,
    )


def _log_reconciliada(cd_liq: CdLiquidacion, resultado: ReconciliarLiquidacionResultado) -> None:
    """Solo deja rastro cuando la reconciliación aplicó algo (diff de incidentes,
    estado, extra o factura); las revisiones sin novedad no ensucian el log."""
    novedades = (
        resultado.altas, resultado.cambios, resultado.bajas,
        resultado.estado_actualizado, resultado.extra_actualizado, resultado.factura_actualizada,
    )
    if not (resultado.reconciliada and any(novedades)):
        return
    logger.info(
        "sync CD: %s reconciliada — %d altas, %d cambios, %d bajas, "
        "estado actualizado=%s, extra actualizado=%s, factura actualizada=%s",
        cd_liq.numero_liquidacion,
        resultado.altas,
        resultado.cambios,
        resultado.bajas,
        resultado.estado_actualizado,
        resultado.extra_actualizado,
        resultado.factura_actualizada,
    )
