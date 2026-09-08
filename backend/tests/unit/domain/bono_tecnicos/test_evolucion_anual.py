from src.modules.bono_tecnicos.domain.entities.conteo_tecnico import ConteoTecnico
from src.modules.bono_tecnicos.domain.services.evolucion_anual import (
    promedio_equipo,
    serie_anual,
)
from src.modules.bono_tecnicos.domain.value_objects.conteo_tv import ConteoTv


def _conteo(periodo: int, correctivo: int = 10) -> ConteoTecnico:
    return ConteoTecnico(
        tecnico="CD - Ana",
        id_tecnico=1,
        periodo=periodo,
        correctivo=correctivo,
        preventivo=0,
        inst_des=0,
        pre_correctivo=0,
        entrega_insumos=0,
    )


def test_serie_anual_siempre_tiene_los_12_meses() -> None:
    serie = serie_anual(2026, 1, "CD - Ana", [], {}, {})

    assert [p.periodo for p in serie] == [202601 + i for i in range(12)]


def test_mes_sin_dias_cargados_queda_con_puntaje_none() -> None:
    conteo = _conteo(202605, correctivo=10)

    serie = serie_anual(2026, 1, "CD - Ana", [conteo], {}, {})

    punto_mayo = next(p for p in serie if p.periodo == 202605)
    assert punto_mayo.puntaje is None
    assert punto_mayo.incidentes == 10


def test_mes_sin_incidentes_pero_con_dias_da_puntaje_cero() -> None:
    serie = serie_anual(2026, 1, "CD - Ana", [], {202605: 15}, {})

    punto_mayo = next(p for p in serie if p.periodo == 202605)
    assert punto_mayo.puntaje == 0
    assert punto_mayo.incidentes == 0


def test_tv_solicitadas_y_aprobadas_del_mes() -> None:
    serie = serie_anual(
        2026, 1, "CD - Ana", [], {202605: 10}, {202605: ConteoTv(solicitadas=3, aprobadas=2)}
    )

    punto_mayo = next(p for p in serie if p.periodo == 202605)
    assert punto_mayo.tv_solicitadas == 3
    assert punto_mayo.tv_aprobadas == 2


def test_promedio_equipo_ignora_meses_sin_puntaje() -> None:
    serie_ana = serie_anual(2026, 1, "CD - Ana", [_conteo(202605)], {202605: 10}, {})
    serie_beto = serie_anual(2026, 2, "CD - Beto", [_conteo(202605)], {}, {})

    equipo = promedio_equipo([serie_ana, serie_beto])

    punto_mayo = next(p for p in equipo if p.periodo == 202605)
    # Solo Ana tiene Días cargados en mayo; Beto (sin Días) no cuenta en el promedio.
    assert punto_mayo.puntaje == serie_ana[4].puntaje


def test_promedio_equipo_de_lista_vacia_es_lista_vacia() -> None:
    assert promedio_equipo([]) == []
