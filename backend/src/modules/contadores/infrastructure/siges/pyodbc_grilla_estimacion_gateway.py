"""Adapter pyodbc del puerto GrillaEstimacionPort — la consulta central del
Estimador (MODELO_DE_DATOS.md §3.4). El SQL es el real del proyecto original
(`grilla_estimacion_query.py`); acá solo se mapea el resultado posicional
(0-73) a `FilaGrillaSigesDto`, en el mismo orden que documenta el .sql."""

import asyncio
import time
from datetime import date, datetime
from typing import Any

from src.modules.contadores.application.dtos.fila_grilla_siges_dto import FilaGrillaSigesDto
from src.modules.contadores.infrastructure.siges.grilla_estimacion_query import (
    GRILLA_ESTIMACION_SQL,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner

_GATEWAY = "grilla_estimacion"
# Pipeline de 11 pasos sin los índices recomendados (MIGRACION_SISTEMAS.md §3):
# más margen que el timeout general del runner para clientes medianos/grandes.
_TIMEOUT_SECONDS = 90.0
# TTL largo a propósito (no "liviana, no repetir en cada carga" como el resto
# del módulo): esta consulta es cara (hasta 90s), y "recalcular candidato"
# (RecalcularCandidatoSigesUseCase) reusa el mismo resultado que ya trajo
# `/tablero` en vez de correr el pipeline de nuevo por cada P/L manual que
# prueba el operador durante la misma sesión de trabajo sobre un proceso.
_CACHE_TTL_SECONDS = 600.0


class PyodbcGrillaEstimacionGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner
        self._lock = asyncio.Lock()
        self._cache: dict[tuple[int, date], tuple[float, list[FilaGrillaSigesDto]]] = {}

    async def fetch_grilla(
        self, nro_proceso: int, fecha_objetivo: date
    ) -> list[FilaGrillaSigesDto]:
        clave = (nro_proceso, fecha_objetivo)
        async with self._lock:
            vigente = self._cache.get(clave)
            if vigente is not None and time.monotonic() - vigente[0] < _CACHE_TTL_SECONDS:
                return vigente[1]
        rows = await self._runner.fetch_all(
            GRILLA_ESTIMACION_SQL,
            [nro_proceso, fecha_objetivo],
            gateway=_GATEWAY,
            log_message="Fallo la grilla de estimación contra Siges/MERCURIO",
            log_extra={"nro_proceso": nro_proceso, "fecha_objetivo": str(fecha_objetivo)},
            timeout_override=_TIMEOUT_SECONDS,
        )
        filas = [_fila_de(row) for row in rows]
        async with self._lock:
            self._cache[clave] = (time.monotonic(), filas)
        return filas


def _fila_de(row: Any) -> FilaGrillaSigesDto:
    return FilaGrillaSigesDto(
        **_identidad_de(row),
        **_lecturas_de(row),
        **_parque_de(row),
        **_periodo_estado_de(row),
        historico=_historico_de(row),
        **_actual_metadata_de(row),
        **_auditoria_parque_de(row),
        ultimo_real_no_t4_fecha=_d(row[73]),
    )


def _identidad_de(row: Any) -> dict[str, Any]:
    return dict(
        id_maquina=int(row[0]),
        id_clase_contador=int(row[1]),
        nro_serie=str(row[2]),
        id_empresa=int(row[3]),
        empresa_desc=str(row[4]),
        id_sucursal=int(row[5]),
        sucursal_desc=str(row[6]),
        id_sector=int(row[7]) if row[7] is not None else None,
        sector_desc=row[8],
        id_grupo_economico=int(row[9]),
        id_art_gen=int(row[10]),
        modelo_desc=str(row[11]),
        id_tecnologia=int(row[12]),
        velocidad=float(row[13]) if row[13] is not None else None,
    )


def _lecturas_de(row: Any) -> dict[str, Any]:
    return dict(
        pendiente_estimar=bool(row[14]),
        contador_anterior_valor=_f(row[15]),
        contador_anterior_fecha=_d(row[16]),
        contador_anterior_tipo_toma=row[17],
        ultimo_real_valor=_f(row[18]),
        ultimo_real_fecha=_d(row[19]),
        ultimo_real_tipo_toma=row[20],
        real_anterior_valor=_f(row[21]),
        real_anterior_fecha=_d(row[22]),
        real_anterior_tipo_toma=row[23],
        t4st_valor=_f(row[24]),
        t4st_fecha=_d(row[25]),
        t4st_para_facturar=bool(row[26]),
    )


def _parque_de(row: Any) -> dict[str, Any]:
    return dict(
        prom_6_fc=_f(row[27]),
        prom_parque_cliente_tec=_f(row[28]),
        cnt_parque_cliente_tec=int(row[29] or 0),
        prom_parque_cliente_modelo=_f(row[30]),
        prom_parque_grupo_modelo=_f(row[31]),
        prom_parque_global_modelo=_f(row[32]),
        q1_parque_cliente_tec=_f(row[34]),
        q3_parque_cliente_tec=_f(row[35]),
    )


def _periodo_estado_de(row: Any) -> dict[str, Any]:
    return dict(
        periodo_hasta=_d(row[36]),
        periodo_desde=_d(row[37]),
        id_estado_maquina=int(row[38]),
        estado_maquina_desc=row[39],
    )


def _historico_de(row: Any) -> tuple[float, ...]:
    return tuple(float(row[i] or 0) for i in range(40, 51))


def _actual_metadata_de(row: Any) -> dict[str, Any]:
    return dict(
        fc_impre_contador_actual=_f(row[51]),
        fc_impresiones_reales=_f(row[54]),
        empresa_actual_desc=row[55],
        id_modo_oper=int(row[56]),
        es_clase_sintetica=bool(row[57]),
    )


def _auditoria_parque_de(row: Any) -> dict[str, Any]:
    return dict(
        pct_cnt_descartados=int(row[58] or 0),
        pct_mediana_cruda=_f(row[59]),
        pct_media_cruda=_f(row[60]),
        pcm_cnt_descartados=int(row[61] or 0),
        pcm_cant=int(row[62] or 0),
        pcm_mediana_cruda=_f(row[63]),
        pcm_media_cruda=_f(row[64]),
        pgm_cnt_descartados=int(row[65] or 0),
        pgm_cant=int(row[66] or 0),
        pgm_mediana_cruda=_f(row[67]),
        pgm_media_cruda=_f(row[68]),
        pgl_cnt_descartados=int(row[69] or 0),
        pgl_cant=int(row[70] or 0),
        pgl_mediana_cruda=_f(row[71]),
        pgl_media_cruda=_f(row[72]),
    )


def _f(valor: Any) -> float | None:
    return float(valor) if valor is not None else None


def _d(valor: date | datetime | None) -> date | None:
    """pyodbc/FreeTDS devuelve una columna SQL `date` como `datetime.datetime`
    (hora 00:00:00), no como `date` — el motor hace aritmética asumiendo
    `date` puro (bug real visto 2026-09-05: `date - datetime` no se puede)."""
    if isinstance(valor, datetime):
        return valor.date()
    return valor
