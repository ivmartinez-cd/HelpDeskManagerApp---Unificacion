"""Serie mensual de un técnico a lo largo de un año calendario, y el promedio
del equipo — la vista de gerencia necesita los 12 meses siempre presentes
(un mes sin incidentes o sin Días cargados es un hueco en el gráfico, no una
fila ausente), igual que `fill_daily_series` en insumos."""

from dataclasses import dataclass

from src.modules.bono_tecnicos.domain.entities.conteo_tecnico import ConteoTecnico
from src.modules.bono_tecnicos.domain.services.calculador_puntaje import calcular_puntaje
from src.modules.bono_tecnicos.domain.value_objects.conteo_tv import ConteoTv
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo, periodos_del_anio

_DECIMALES = 2


@dataclass(frozen=True, slots=True)
class PuntoMensual:
    periodo: int
    puntaje: float | None
    incidentes: float
    dias: float
    tv_solicitadas: float
    tv_aprobadas: float


def serie_anual(
    anio: int,
    id_tecnico: int,
    tecnico: str,
    conteos: list[ConteoTecnico],
    dias_por_periodo: dict[int, float],
    tv_por_periodo: dict[int, ConteoTv],
) -> list[PuntoMensual]:
    """Los 12 puntos del año — un mes sin conteos se completa en cero en vez
    de saltarse, así `puntaje` solo queda `None` por falta de Días cargados."""
    conteos_por_periodo = {c.periodo: c for c in conteos}
    return [
        _punto_de(p, conteos_por_periodo, tecnico, id_tecnico, dias_por_periodo, tv_por_periodo)
        for p in periodos_del_anio(anio)
    ]


def _punto_de(
    periodo: Periodo,
    conteos_por_periodo: dict[int, ConteoTecnico],
    tecnico: str,
    id_tecnico: int,
    dias_por_periodo: dict[int, float],
    tv_por_periodo: dict[int, ConteoTv],
) -> PuntoMensual:
    vacio = _conteo_vacio(tecnico, id_tecnico, periodo.value)
    conteo = conteos_por_periodo.get(periodo.value) or vacio
    dias = dias_por_periodo.get(periodo.value, 0.0)
    tv = tv_por_periodo.get(periodo.value, ConteoTv(0, 0))
    return PuntoMensual(
        periodo=periodo.value,
        puntaje=calcular_puntaje(conteo, dias, tv.aprobadas),
        incidentes=_total_incidentes(conteo),
        dias=dias,
        tv_solicitadas=tv.solicitadas,
        tv_aprobadas=tv.aprobadas,
    )


def _conteo_vacio(tecnico: str, id_tecnico: int, periodo: int) -> ConteoTecnico:
    return ConteoTecnico(
        tecnico=tecnico,
        id_tecnico=id_tecnico,
        periodo=periodo,
        correctivo=0,
        preventivo=0,
        inst_des=0,
        pre_correctivo=0,
        entrega_insumos=0,
    )


def promedio_equipo(series: list[list[PuntoMensual]]) -> list[PuntoMensual]:
    """Promedio mes a mes de todos los técnicos — la serie gris punteada de
    referencia en el gráfico. Un técnico sin puntaje ese mes (sin Días
    cargados) no cuenta en el promedio de ese mes en particular, en vez de
    tratarlo como 0 y hundir artificialmente el promedio del equipo."""
    if not series:
        return []
    return [
        PuntoMensual(
            periodo=puntos_del_mes[0].periodo,
            puntaje=_promedio(
                [p.puntaje for p in puntos_del_mes if p.puntaje is not None], _DECIMALES
            ),
            incidentes=_promedio([p.incidentes for p in puntos_del_mes], 1) or 0.0,
            dias=_promedio([p.dias for p in puntos_del_mes], 1) or 0.0,
            tv_solicitadas=_promedio([p.tv_solicitadas for p in puntos_del_mes], 1) or 0.0,
            tv_aprobadas=_promedio([p.tv_aprobadas for p in puntos_del_mes], 1) or 0.0,
        )
        for puntos_del_mes in zip(*series, strict=True)
    ]


def _total_incidentes(conteo: ConteoTecnico) -> float:
    return (
        conteo.correctivo
        + conteo.preventivo
        + conteo.inst_des
        + conteo.pre_correctivo
        + conteo.entrega_insumos
    )


def _promedio(valores: list[float], decimales: int) -> float | None:
    return round(sum(valores) / len(valores), decimales) if valores else None
