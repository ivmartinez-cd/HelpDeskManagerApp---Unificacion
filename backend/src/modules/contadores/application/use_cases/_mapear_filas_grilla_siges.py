"""Agrupa las filas crudas de `GRILLA_ESTIMACION_SQL` (una por equipo+clase)
en `EquipoProceso` (una por equipo, con sus clases) — la forma que ya espera
el resto del pipeline (`construir_estimacion_input`, `estimar()`). Mismo
criterio de lectura que `EquipoGrillaRaw` del legacy: un dato que Siges no
tiene llega como `None`, nunca como un valor inventado."""

from dataclasses import dataclass
from datetime import date
from typing import TypedDict

from src.modules.contadores.application.dtos.equipo_proceso_dto import (
    ClaseProceso,
    EquipoProceso,
)
from src.modules.contadores.application.dtos.fila_grilla_siges_dto import FilaGrillaSigesDto
from src.modules.contadores.application.dtos.parque_historico_dto import (
    NivelParqueHistorico,
    ParqueHistorico,
)
from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import (
    EstadoMaquina,
    Tecnologia,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef
from src.modules.contadores.domain.value_objects.estimacion.promedio_parque import PromedioParque

_TIPO_TOMA_T4 = 4
_IDS_ESTADO_BACKUP = (3, 8)
_ID_ESTADO_EN_TRANSITO = 200
_ID_TECNOLOGIA_MONO = 1


def agrupar_por_equipo(filas: list[FilaGrillaSigesDto]) -> list[EquipoProceso]:
    # Legacy (`GrillaEstimacion.razor` `RecalcularGrupos`): `GroupBy(ID_Maquina)`
    # conserva el orden de primera aparición (el `ORDER BY` de la SQL: empresa,
    # sucursal, nro de serie) y solo ordena las clases dentro de cada equipo
    # por `ID_ClaseContador` (Cl.10 antes que Cl.20).
    por_maquina: dict[int, list[FilaGrillaSigesDto]] = {}
    for fila in filas:
        por_maquina.setdefault(fila.id_maquina, []).append(fila)
    return [
        _equipo_de(id_maquina, sorted(filas_equipo, key=lambda f: f.id_clase_contador))
        for id_maquina, filas_equipo in por_maquina.items()
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
        estado_maquina_desc=primera.estado_maquina_desc or "",
        empresa_actual_desc=primera.empresa_actual_desc,
        id_art_gen=primera.id_art_gen,
        id_modo_oper=primera.id_modo_oper,
    )


def _estado_maquina_de(id_estado: int) -> EstadoMaquina:
    if id_estado in _IDS_ESTADO_BACKUP:
        return "BACKUP"
    if id_estado == _ID_ESTADO_EN_TRANSITO:
        return "EN_TRANSITO"
    return "NORMAL"


def tecnologia_de(id_tecnologia: int) -> Tecnologia:
    """Legacy (`CalculadorContadores`, `GrillaEstimacion`): `IdTecnologia == 1`
    es Mono; cualquier otro valor se trata como Color."""
    return "MONO" if id_tecnologia == _ID_TECNOLOGIA_MONO else "COLOR"


def _clase_de(f: FilaGrillaSigesDto) -> ClaseProceso:
    return ClaseProceso(
        clase=str(f.id_clase_contador),
        tecnologia=tecnologia_de(f.id_tecnologia),
        velocidad_ppm=f.velocidad,
        prom_6_facturados=f.prom_6_fc,
        historico_12=_historico_con_placeholder(f),
        es_clase_sintetica=f.es_clase_sintetica,
        prom_global_modelo_imp=f.prom_global_modelo_imp,
        parque_historico=_parque_historico_de(f),
        **_real_cargado_de(f),
        **_lecturas_de(f),
        **_parques_de(f),
    )


def _parque_historico_de(f: FilaGrillaSigesDto) -> ParqueHistorico:
    return ParqueHistorico(
        cliente_modelo=NivelParqueHistorico(
            f.pcm_cant, f.prom_parque_cliente_modelo, f.pcm_mediana_cruda
        ),
        grupo_modelo=NivelParqueHistorico(
            f.pgm_cant, f.prom_parque_grupo_modelo, f.pgm_mediana_cruda
        ),
        cliente_tec=NivelParqueHistorico(
            f.cnt_parque_cliente_tec, f.prom_parque_cliente_tec, f.pct_mediana_cruda
        ),
        global_modelo=NivelParqueHistorico(
            f.pgl_cant, f.prom_parque_global_modelo, f.pgl_mediana_cruda
        ),
    )


def _historico_con_placeholder(f: FilaGrillaSigesDto) -> tuple[float, ...]:
    """H11..H01 (viejo → reciente) + el mes actual al final, como el BarChart
    del legacy (11 barras de historia + la del período). El placeholder del
    mes actual se completa con el resultado del motor en el tablero."""
    return (*f.historico, 0.0)


class _RealCargadoKwargs(TypedDict):
    ya_real: bool
    valor_real_cargado: float | None
    impresiones_reales: float | None
    tipo_toma_actual: int | None
    fecha_toma_actual: date | None


def _real_cargado_de(f: FilaGrillaSigesDto) -> _RealCargadoKwargs:
    """Lectura real ya cargada en el proceso: el legacy muestra como
    impresiones `FC_ImpresionesReales` (col 54) y la fecha/tipo del contador
    actual (cols 52/53) — todas NULL si la fila todavía falta estimar."""
    ya_real = not f.pendiente_estimar
    return _RealCargadoKwargs(
        ya_real=ya_real,
        valor_real_cargado=f.fc_impre_contador_actual if ya_real else None,
        impresiones_reales=f.fc_impresiones_reales,
        tipo_toma_actual=f.fc_tipo_toma_cont_actual,
        fecha_toma_actual=f.fc_fecha_cont_actual,
    )


class _LecturasKwargs(TypedDict):
    ultimo_contador_facturado: LecturaRef | None
    ultimo_real: LecturaRef | None
    fecha_ultimo_real_no_t4: date | None
    real_anterior: LecturaRef | None
    t4_mas_reciente: LecturaRef | None
    t4_revisado: bool


class _ParquesKwargs(TypedDict):
    parque_cliente_modelo: PromedioParque | None
    parque_grupo_modelo: PromedioParque | None
    parque_cliente_tecnologia: PromedioParque | None
    parque_global_modelo: PromedioParque | None


def _lecturas_de(f: FilaGrillaSigesDto) -> _LecturasKwargs:
    return _LecturasKwargs(
        ultimo_contador_facturado=_lectura(
            f.contador_anterior_valor, f.contador_anterior_fecha, f.contador_anterior_tipo_toma
        ),
        ultimo_real=_lectura(f.ultimo_real_valor, f.ultimo_real_fecha, f.ultimo_real_tipo_toma),
        fecha_ultimo_real_no_t4=f.ultimo_real_no_t4_fecha,
        real_anterior=_lectura(
            f.real_anterior_valor, f.real_anterior_fecha, f.real_anterior_tipo_toma
        ),
        t4_mas_reciente=_lectura(f.t4st_valor, f.t4st_fecha, _TIPO_TOMA_T4),
        t4_revisado=f.t4st_para_facturar,
    )


def _parques_de(f: FilaGrillaSigesDto) -> _ParquesKwargs:
    return _ParquesKwargs(
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


def _lectura(
    valor: float | None, fecha: date | None, tipo_toma: int | None
) -> LecturaRef | None:
    """`None` si Siges no trae la lectura — incluido el contador anterior de
    un equipo sin ningún facturado previo: el legacy lo deja NULL y el motor
    decide (`GetValueOrDefault()`, `ContadorAnterior ?? UltimoReal ?? 0`).
    Valor, fecha y tipo salen de la misma fila de `Contadores`; un tipo NULL
    suelto se lee como 0, igual que `TipoToma.GetValueOrDefault()`."""
    if valor is None or fecha is None:
        return None
    return LecturaRef(valor, fecha, tipo_toma or 0)


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
