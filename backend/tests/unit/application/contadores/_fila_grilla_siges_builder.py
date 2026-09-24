"""Builder de `FilaGrillaSigesDto` para tests: una fila mínima válida de la
grilla de Siges (equipo Mono a estimar, sin parque) que cada test pisa con
`replace(...)` o con kwargs."""

from dataclasses import replace
from datetime import date
from typing import Any

from src.modules.contadores.application.dtos.fila_grilla_siges_dto import FilaGrillaSigesDto

PERIODO_DESDE = date(2026, 4, 1)
PERIODO_HASTA = date(2026, 5, 1)

_BASE = FilaGrillaSigesDto(
    id_maquina=101, id_clase_contador=10, nro_serie="SER1",
    id_empresa=5, empresa_desc="Empresa", id_sucursal=7, sucursal_desc="Sucursal",
    id_sector=None, sector_desc=None, id_grupo_economico=900, id_art_gen=55,
    modelo_desc="Modelo X", id_tecnologia=1, velocidad=45.0,
    pendiente_estimar=True,
    contador_anterior_valor=1_000.0, contador_anterior_fecha=date(2026, 3, 31),
    contador_anterior_tipo_toma=1,
    ultimo_real_valor=None, ultimo_real_fecha=None, ultimo_real_tipo_toma=None,
    real_anterior_valor=None, real_anterior_fecha=None, real_anterior_tipo_toma=None,
    t4st_valor=None, t4st_fecha=None, t4st_para_facturar=False,
    prom_6_fc=None, prom_parque_cliente_tec=None, cnt_parque_cliente_tec=0,
    prom_parque_cliente_modelo=None, prom_parque_grupo_modelo=None,
    prom_parque_global_modelo=None, q1_parque_cliente_tec=None, q3_parque_cliente_tec=None,
    periodo_hasta=PERIODO_HASTA, periodo_desde=PERIODO_DESDE,
    id_estado_maquina=1, estado_maquina_desc="Instalada",
    historico=tuple(float(i) for i in range(11, 0, -1)),
    fc_impresiones_reales=None, empresa_actual_desc=None, fc_impre_contador_actual=None,
    id_modo_oper=1, es_clase_sintetica=False,
    pct_cnt_descartados=0, pct_mediana_cruda=None, pct_media_cruda=None,
    pcm_cnt_descartados=0, pcm_cant=0, pcm_mediana_cruda=None, pcm_media_cruda=None,
    pgm_cnt_descartados=0, pgm_cant=0, pgm_mediana_cruda=None, pgm_media_cruda=None,
    pgl_cnt_descartados=0, pgl_cant=0, pgl_mediana_cruda=None, pgl_media_cruda=None,
    ultimo_real_no_t4_fecha=None,
)


def fila_siges(**cambios: Any) -> FilaGrillaSigesDto:
    return replace(_BASE, **cambios)
