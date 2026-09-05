"""Agrupa las filas crudas de `GRILLA_ESTIMACION_SQL` (una por equipo+clase)
en `EquipoProceso` (una por equipo, con sus clases) — la forma que ya espera
el resto del pipeline (`construir_estimacion_input`, `estimar()`)."""

from dataclasses import dataclass
from itertools import groupby

from src.modules.contadores.application.dtos.equipo_proceso_dto import (
    ClaseProceso,
    EquipoProceso,
)
from src.modules.contadores.application.dtos.fila_grilla_siges_dto import FilaGrillaSigesDto
from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import (
    EstadoMaquina,
    Tecnologia,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef
from src.modules.contadores.domain.value_objects.estimacion.promedio_parque import PromedioParque

_TIPO_TOMA_T4 = 4
_IDS_ESTADO_BACKUP = (3, 8)
_ID_ESTADO_EN_TRANSITO = 200


def agrupar_por_equipo(filas: list[FilaGrillaSigesDto]) -> list[EquipoProceso]:
    filas_ordenadas = sorted(filas, key=lambda f: f.id_maquina)
    return [
        _equipo_de(id_maquina, list(filas_equipo))
        for id_maquina, filas_equipo in groupby(filas_ordenadas, key=lambda f: f.id_maquina)
    ]


def _equipo_de(id_maquina: int, filas_equipo: list[FilaGrillaSigesDto]) -> EquipoProceso:
    primera = filas_equipo[0]
    return EquipoProceso(
        id_maquina=id_maquina,
        nro_serie=primera.nro_serie,
        empresa=primera.empresa_desc,
        sucursal=primera.sucursal_desc,
        sector=primera.sector_desc or "",
        modelo=primera.modelo_desc,
        estado_maquina=_estado_maquina_de(primera.id_estado_maquina),
        clases=tuple(_clase_de(f) for f in filas_equipo),
    )


def _estado_maquina_de(id_estado: int) -> EstadoMaquina:
    if id_estado in _IDS_ESTADO_BACKUP:
        return "BACKUP"
    if id_estado == _ID_ESTADO_EN_TRANSITO:
        return "EN_TRANSITO"
    return "NORMAL"


def _tecnologia_de(id_tecnologia: int) -> Tecnologia:
    return "COLOR" if id_tecnologia == 2 else "MONO"


def _clase_de(f: FilaGrillaSigesDto) -> ClaseProceso:
    ya_real = not f.pendiente_estimar
    return ClaseProceso(
        clase=str(f.id_clase_contador),
        tecnologia=_tecnologia_de(f.id_tecnologia),
        velocidad_ppm=f.velocidad,
        ultimo_contador_facturado=_ultimo_facturado_de(f),
        ya_real=ya_real,
        valor_real_cargado=f.fc_impre_contador_actual if ya_real else None,
        prom_6_facturados=f.prom_6_fc,
        # Placeholder: el mes actual se completa después con el resultado real
        # del motor (`_historico_con_actual`, get_tablero_proyeccion.py).
        historico_12=(*f.historico, 0.0),
        es_clase_sintetica=f.es_clase_sintetica,
        **_lecturas_de(f),
        **_parques_de(f),
    )


def _lecturas_de(f: FilaGrillaSigesDto) -> dict[str, object]:
    return dict(
        ultimo_real=_lectura(f.ultimo_real_valor, f.ultimo_real_fecha, f.ultimo_real_tipo_toma),
        fecha_ultimo_real_no_t4=f.ultimo_real_no_t4_fecha,
        real_anterior=_lectura(
            f.real_anterior_valor, f.real_anterior_fecha, f.real_anterior_tipo_toma
        ),
        t4_mas_reciente=_lectura(f.t4st_valor, f.t4st_fecha, _TIPO_TOMA_T4),
        t4_revisado=f.t4st_para_facturar,
    )


def _parques_de(f: FilaGrillaSigesDto) -> dict[str, PromedioParque | None]:
    return dict(
        parque_cliente_modelo=_promedio(_StatsNivel(
            f.prom_parque_cliente_modelo, f.pcm_cant, f.pcm_cnt_descartados,
            f.pcm_mediana_cruda, f.pcm_media_cruda,
        )),
        parque_grupo_modelo=_promedio(_StatsNivel(
            f.prom_parque_grupo_modelo, f.pgm_cant, f.pgm_cnt_descartados,
            f.pgm_mediana_cruda, f.pgm_media_cruda,
        )),
        parque_cliente_tecnologia=_promedio(_StatsNivel(
            f.prom_parque_cliente_tec, f.cnt_parque_cliente_tec, f.pct_cnt_descartados,
            f.pct_mediana_cruda, f.pct_media_cruda,
            f.q1_parque_cliente_tec, f.q3_parque_cliente_tec,
        )),
        parque_global_modelo=_promedio(_StatsNivel(
            f.prom_parque_global_modelo, f.pgl_cant, f.pgl_cnt_descartados,
            f.pgl_mediana_cruda, f.pgl_media_cruda,
        )),
    )


def _ultimo_facturado_de(f: FilaGrillaSigesDto) -> LecturaRef:
    if f.contador_anterior_valor is not None:
        return LecturaRef(
            f.contador_anterior_valor, f.contador_anterior_fecha, f.contador_anterior_tipo_toma
        )
    # Equipo sin ningún contador facturado antes (nuevo en el parque): el
    # motor necesita un ancla igual, 0 en la apertura del período es la
    # aproximación más razonable — no hay dato mejor en SiGes para este caso.
    return LecturaRef(0.0, f.periodo_desde, 1)


def _lectura(valor: float | None, fecha: object, tipo_toma: int | None) -> LecturaRef | None:
    if valor is None:
        return None
    return LecturaRef(valor, fecha, tipo_toma)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class _StatsNivel:
    valor: float | None
    n_equipos: int
    n_descartados: int
    mediana_cruda: float | None
    media_cruda: float | None
    q1: float | None = None
    q3: float | None = None


def _promedio(stats: _StatsNivel) -> PromedioParque | None:
    if stats.valor is None:
        return None
    return PromedioParque(
        stats.valor, stats.n_equipos, stats.n_descartados,
        stats.mediana_cruda, stats.media_cruda, stats.q1, stats.q3,
    )
