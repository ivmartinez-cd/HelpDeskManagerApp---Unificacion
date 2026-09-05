from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class FilaGrillaSigesDto:
    """Una fila cruda del SELECT final de `GRILLA_ESTIMACION_SQL` — mismo
    orden posicional 0-73 que documenta el .sql original (`SiGesRepository`
    en el código .NET también lee por índice, no por nombre)."""

    id_maquina: int
    id_clase_contador: int
    nro_serie: str
    id_empresa: int
    empresa_desc: str
    id_sucursal: int
    sucursal_desc: str
    id_sector: int | None
    sector_desc: str | None
    id_grupo_economico: int
    id_art_gen: int
    modelo_desc: str
    id_tecnologia: int
    velocidad: float | None
    pendiente_estimar: bool
    contador_anterior_valor: float | None
    contador_anterior_fecha: date | None
    contador_anterior_tipo_toma: int | None
    ultimo_real_valor: float | None
    ultimo_real_fecha: date | None
    ultimo_real_tipo_toma: int | None
    real_anterior_valor: float | None
    real_anterior_fecha: date | None
    real_anterior_tipo_toma: int | None
    t4st_valor: float | None
    t4st_fecha: date | None
    t4st_para_facturar: bool
    prom_6_fc: float | None
    prom_parque_cliente_tec: float | None
    cnt_parque_cliente_tec: int
    prom_parque_cliente_modelo: float | None
    prom_parque_grupo_modelo: float | None
    prom_parque_global_modelo: float | None
    q1_parque_cliente_tec: float | None
    q3_parque_cliente_tec: float | None
    periodo_hasta: date
    periodo_desde: date
    id_estado_maquina: int
    estado_maquina_desc: str | None
    historico: tuple[float, ...]
    fc_impresiones_reales: float | None
    empresa_actual_desc: str | None
    fc_impre_contador_actual: float | None
    id_modo_oper: int
    es_clase_sintetica: bool
    pct_cnt_descartados: int
    pct_mediana_cruda: float | None
    pct_media_cruda: float | None
    pcm_cnt_descartados: int
    pcm_cant: int
    pcm_mediana_cruda: float | None
    pcm_media_cruda: float | None
    pgm_cnt_descartados: int
    pgm_cant: int
    pgm_mediana_cruda: float | None
    pgm_media_cruda: float | None
    pgl_cnt_descartados: int
    pgl_cant: int
    pgl_mediana_cruda: float | None
    pgl_media_cruda: float | None
    ultimo_real_no_t4_fecha: date | None
