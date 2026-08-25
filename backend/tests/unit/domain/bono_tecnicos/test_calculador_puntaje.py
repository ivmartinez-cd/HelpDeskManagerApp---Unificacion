from src.modules.bono_tecnicos.domain.entities.conteo_tecnico import ConteoTecnico
from src.modules.bono_tecnicos.domain.services.calculador_puntaje import calcular_puntaje


def _conteo(**overrides: int) -> ConteoTecnico:
    base = {
        "tecnico": "CD - Agustin HACZEK",
        "id_tecnico": 1314,
        "periodo": 202605,
        "correctivo": 0,
        "preventivo": 0,
        "inst_des": 0,
        "pre_correctivo": 0,
        "entrega_insumos": 0,
    }
    base.update(overrides)
    return ConteoTecnico(**base)  # type: ignore[arg-type]


def test_replica_el_puntaje_del_excel_de_mayo_haczek() -> None:
    # Lista!I1:J9 de "Tecnicos.xlsx": Correctivo 47, Preventivo 44, InstDes 4,
    # PreCorrectivo 1, EntregaInsumos 22, TV 25, Días 17 -> Puntaje 7,4764...
    conteo = _conteo(
        correctivo=47, preventivo=44, inst_des=4, pre_correctivo=1, entrega_insumos=22
    )

    assert calcular_puntaje(conteo, dias=17, tareas_varias=25) == 7.48


def test_pesos_de_preventivo_y_pre_correctivo() -> None:
    conteo = _conteo(preventivo=10, pre_correctivo=10)

    # (10*0.65 + 10*0.5) / 1 = 11.5
    assert calcular_puntaje(conteo, dias=1, tareas_varias=0) == 11.5


def test_sin_dias_no_calcula_puntaje() -> None:
    conteo = _conteo(correctivo=5)

    assert calcular_puntaje(conteo, dias=0, tareas_varias=0) is None


def test_dias_negativos_no_calcula_puntaje() -> None:
    conteo = _conteo(correctivo=5)

    assert calcular_puntaje(conteo, dias=-1, tareas_varias=0) is None


def test_admite_medio_dia() -> None:
    conteo = _conteo(correctivo=41)

    # 41 / 20.5 = 2.0
    assert calcular_puntaje(conteo, dias=20.5, tareas_varias=0) == 2.0
