"""Adapter pyodbc del puerto GrillaEstimacionPort — la consulta central del
Estimador (MODELO_DE_DATOS.md §3.4). El SQL es el real del proyecto original
(`grilla_estimacion_query.py`); acá solo se mapea el resultado posicional
(0-73) a `FilaGrillaSigesDto`, en el mismo orden y con los mismos defaults
ante NULL que `SiGesRepository.GetGrillaAsync` del legacy."""

from datetime import date, datetime
from typing import Any

from src.modules.contadores.application.dtos.fila_grilla_siges_dto import FilaGrillaSigesDto
from src.modules.contadores.infrastructure.siges.grilla_estimacion_query import (
    GRILLA_ESTIMACION_SQL,
)
from src.shared.infrastructure.orion.query_runner import OrionQueryRunner

_GATEWAY = "grilla_estimacion"
# Legacy v1.7 (`SiGesRepository.GetGrillaAsync`): `CommandTimeout = 180` —
# pipeline de 11 pasos, lento en clientes grandes.
_TIMEOUT_SECONDS = 180.0
# Tope de grillas recordadas (una por (operador, proceso, fecha objetivo)):
# solo acota memoria, no es una política de vigencia.
_MAX_GRILLAS_RECORDADAS = 32
_Clave = tuple[str | None, int, date]


class PyodbcGrillaEstimacionGateway:
    """Igual que el legacy (`Index.CargarTablero` consulta Siges en cada
    carga y el resto de la pantalla trabaja sobre esa lista en memoria):
    `fresca=True` (la carga del tablero) siempre va a Siges; el resto de las
    llamadas del mismo proceso (candidatos, recalcular, forzar, export)
    reusan la última grilla cargada, y solo consultan si no hay ninguna.
    La grilla recordada es la de CADA operador (en v1.7 cada circuito Blazor
    tiene su propia lista): la recarga de otro operador no cambia lo que
    calculan el panel, la vista previa y el CSV de este. Es memoria del
    proceso: con varios workers de uvicorn cada uno tiene la suya."""

    def __init__(self, runner: OrionQueryRunner) -> None:
        self._runner = runner
        self._ultima_carga: dict[_Clave, list[FilaGrillaSigesDto]] = {}

    async def fetch_grilla(
        self,
        nro_proceso: int,
        fecha_objetivo: date,
        *,
        fresca: bool = False,
        operador: str | None = None,
    ) -> list[FilaGrillaSigesDto]:
        clave = (operador, nro_proceso, fecha_objetivo)
        cargada = None if fresca else self._ultima_carga.get(clave)
        if cargada is not None:
            return cargada
        filas = await self._consultar(nro_proceso, fecha_objetivo)
        self._recordar(clave, filas)
        return filas

    async def _consultar(
        self, nro_proceso: int, fecha_objetivo: date
    ) -> list[FilaGrillaSigesDto]:
        rows = await self._runner.fetch_all(
            GRILLA_ESTIMACION_SQL,
            [nro_proceso, fecha_objetivo],
            gateway=_GATEWAY,
            log_message="Fallo la grilla de estimación contra Siges/ORION",
            log_extra={"nro_proceso": nro_proceso, "fecha_objetivo": str(fecha_objetivo)},
            timeout_override=_TIMEOUT_SECONDS,
        )
        return [_fila_de(row) for row in rows]

    def _recordar(self, clave: _Clave, filas: list[FilaGrillaSigesDto]) -> None:
        self._ultima_carga.pop(clave, None)
        self._ultima_carga[clave] = filas
        while len(self._ultima_carga) > _MAX_GRILLAS_RECORDADAS:
            del self._ultima_carga[next(iter(self._ultima_carga))]


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
        nro_serie=_s(row[2]),
        id_empresa=int(row[3]),
        empresa_desc=_s(row[4]),
        id_sucursal=int(row[5]),
        sucursal_desc=_s(row[6]),
        id_sector=_i(row[7]),
        sector_desc=row[8],
        id_grupo_economico=int(row[9]),
        id_art_gen=int(row[10]),
        modelo_desc=_s(row[11]),
        id_tecnologia=int(row[12]),
        velocidad=_ppm(row[13]),
    )


def _lecturas_de(row: Any) -> dict[str, Any]:
    return dict(
        pendiente_estimar=bool(row[14]),
        contador_anterior_valor=_f(row[15]),
        contador_anterior_fecha=_d(row[16]),
        contador_anterior_tipo_toma=_i(row[17]),
        ultimo_real_valor=_f(row[18]),
        ultimo_real_fecha=_d(row[19]),
        ultimo_real_tipo_toma=_i(row[20]),
        real_anterior_valor=_f(row[21]),
        real_anterior_fecha=_d(row[22]),
        real_anterior_tipo_toma=_i(row[23]),
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
        prom_global_modelo_imp=_f(row[33]),
        q1_parque_cliente_tec=_f(row[34]),
        q3_parque_cliente_tec=_f(row[35]),
    )


def _periodo_estado_de(row: Any) -> dict[str, Any]:
    return dict(
        periodo_hasta=_d(row[36]),
        periodo_desde=_d(row[37]),
        # Legacy: `IsDBNull(38) ? 0 : ...` — un estado NULL no tira la grilla.
        id_estado_maquina=int(row[38] or 0),
        estado_maquina_desc=row[39] or "",
    )


def _historico_de(row: Any) -> tuple[float, ...]:
    """H11..H01 (columnas 50 → 40): del proceso más viejo al más reciente,
    igual que `EquipoGrillaRaw.Historico11` del legacy."""
    return tuple(float(row[i] or 0) for i in range(50, 39, -1))


def _actual_metadata_de(row: Any) -> dict[str, Any]:
    return dict(
        fc_impre_contador_actual=_f(row[51]),
        fc_fecha_cont_actual=_d(row[52]),
        fc_tipo_toma_cont_actual=_i(row[53]),
        fc_impresiones_reales=_f(row[54]),
        empresa_actual_desc=row[55],
        # Legacy: `IsDBNull(56) ? 0 : ...` — mismo criterio que el estado.
        id_modo_oper=int(row[56] or 0),
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


def _s(valor: Any) -> str:
    """`ReadStr` del legacy: NULL → cadena vacía (no el texto "None")."""
    return str(valor) if valor is not None else ""


def _i(valor: Any) -> int | None:
    return int(valor) if valor is not None else None


def _ppm(valor: Any) -> float | None:
    """`ReadIntN` del legacy (`Convert.ToInt32`): la velocidad es un entero de
    ppm; si Siges la trae con decimales se redondea al par más cercano, como
    `Convert.ToInt32(decimal)` (`round` de Python también es bancario)."""
    return float(round(valor)) if valor is not None else None


def _f(valor: Any) -> float | None:
    return float(valor) if valor is not None else None


def _d(valor: date | datetime | None) -> date | None:
    """pyodbc/FreeTDS devuelve una columna SQL `date` como `datetime.datetime`
    (hora 00:00:00), no como `date` — el motor hace aritmética asumiendo
    `date` puro (bug real visto 2026-09-05: `date - datetime` no se puede)."""
    if isinstance(valor, datetime):
        return valor.date()
    return valor
