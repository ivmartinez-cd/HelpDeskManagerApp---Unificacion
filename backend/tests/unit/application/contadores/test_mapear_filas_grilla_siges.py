"""`agrupar_por_equipo`: de filas crudas de Siges a `EquipoProceso`/
`ClaseProceso`, con el criterio de `EquipoGrillaRaw` del legacy — sin
inventar lecturas, tecnología por `IdTecnologia == 1`, lectura real con las
impresiones y el tipo/fecha del contador actual."""

from datetime import date

from src.modules.contadores.application.use_cases._mapear_filas_grilla_siges import (
    agrupar_por_equipo,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef
from tests.unit.application.contadores._fila_grilla_siges_builder import fila_siges


def test_contador_anterior_null_no_se_inventa_una_lectura_en_cero() -> None:
    fila = fila_siges(
        contador_anterior_valor=None, contador_anterior_fecha=None,
        contador_anterior_tipo_toma=None,
    )

    clase = agrupar_por_equipo([fila])[0].clases[0]

    assert clase.ultimo_contador_facturado is None


def test_contador_anterior_presente_se_mapea_tal_cual() -> None:
    clase = agrupar_por_equipo([fila_siges()])[0].clases[0]

    assert clase.ultimo_contador_facturado == LecturaRef(1_000.0, date(2026, 3, 31), 1)


def test_fila_real_trae_impresiones_reales_y_tipo_fecha_del_contador_actual() -> None:
    fila = fila_siges(
        pendiente_estimar=False, fc_impre_contador_actual=4_800.0,
        fc_impresiones_reales=3_750.0, fc_tipo_toma_cont_actual=22,
        fc_fecha_cont_actual=date(2026, 4, 28),
    )

    clase = agrupar_por_equipo([fila])[0].clases[0]

    assert clase.ya_real is True
    assert clase.valor_real_cargado == 4_800.0
    assert clase.impresiones_reales == 3_750.0
    assert clase.tipo_toma_actual == 22
    assert clase.fecha_toma_actual == date(2026, 4, 28)


def test_fila_a_estimar_no_trae_valor_real_cargado() -> None:
    clase = agrupar_por_equipo([fila_siges(fc_impre_contador_actual=4_800.0)])[0].clases[0]

    assert clase.ya_real is False
    assert clase.valor_real_cargado is None
    assert clase.impresiones_reales is None


def test_tecnologia_uno_es_mono_y_cualquier_otra_color() -> None:
    filas = [
        fila_siges(id_maquina=1, id_tecnologia=1),
        fila_siges(id_maquina=2, id_tecnologia=2),
        fila_siges(id_maquina=3, id_tecnologia=3),
    ]

    tecnologias = [e.clases[0].tecnologia for e in agrupar_por_equipo(filas)]

    assert tecnologias == ["MONO", "COLOR", "COLOR"]


def test_historico_viejo_a_reciente_con_el_mes_actual_al_final() -> None:
    clase = agrupar_por_equipo([fila_siges()])[0].clases[0]

    assert clase.historico_12 == (11.0, 10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0)


def test_estado_cero_por_null_en_siges_es_normal() -> None:
    assert agrupar_por_equipo([fila_siges(id_estado_maquina=0)])[0].estado_maquina == "NORMAL"


def test_estados_backup_y_en_transito() -> None:
    filas = [
        fila_siges(id_maquina=1, id_estado_maquina=3),
        fila_siges(id_maquina=2, id_estado_maquina=8),
        fila_siges(id_maquina=3, id_estado_maquina=200),
    ]

    estados = [e.estado_maquina for e in agrupar_por_equipo(filas)]

    assert estados == ["BACKUP", "BACKUP", "EN_TRANSITO"]


def test_agrupa_mono_y_color_del_mismo_equipo_ordenando_por_clase() -> None:
    # Legacy `GrillaEstimacion.razor`: GroupBy(ID_Maquina) y dentro del
    # equipo OrderBy(ID_ClaseContador) — Cl.10 antes que Cl.20 aunque Siges
    # las devuelva al revés.
    filas = [
        fila_siges(id_clase_contador=20, id_tecnologia=2),
        fila_siges(id_clase_contador=10, id_tecnologia=2),
    ]

    equipos = agrupar_por_equipo(filas)

    assert len(equipos) == 1
    assert [c.clase for c in equipos[0].clases] == ["10", "20"]


def test_equipos_conservan_el_orden_de_la_sql_no_el_id_de_maquina() -> None:
    # v1.7: la SQL ordena por empresa, sucursal, NroSerie, clase y
    # `GroupBy(ID_Maquina)` conserva el orden de primera aparición (el orden
    # por ubicación es estable) — AAA1 (id 300) antes que ZZZ9 (id 100).
    filas = [
        fila_siges(id_maquina=300, nro_serie="AAA1", id_clase_contador=20, id_tecnologia=2),
        fila_siges(id_maquina=100, nro_serie="ZZZ9", id_clase_contador=10),
        fila_siges(id_maquina=300, nro_serie="AAA1", id_clase_contador=10, id_tecnologia=2),
    ]

    equipos = agrupar_por_equipo(filas)

    assert [e.nro_serie for e in equipos] == ["AAA1", "ZZZ9"]
    assert [c.clase for c in equipos[0].clases] == ["10", "20"]


def test_equipo_lleva_estado_ubicacion_actual_modelo_y_modo_oper_de_siges() -> None:
    fila = fila_siges(
        estado_maquina_desc="Backup", empresa_actual_desc="Otra SA", id_art_gen=77, id_modo_oper=3
    )

    equipo = agrupar_por_equipo([fila])[0]

    assert (equipo.estado_maquina_desc, equipo.empresa_actual_desc) == ("Backup", "Otra SA")
    assert (equipo.id_art_gen, equipo.id_modo_oper) == (77, 3)


def test_sin_cambio_de_empresa_no_hay_ubicacion_actual_y_estado_null_es_vacio() -> None:
    equipo = agrupar_por_equipo([fila_siges(estado_maquina_desc=None)])[0]

    assert equipo.empresa_actual_desc is None
    assert equipo.estado_maquina_desc == ""


def test_t4_se_mapea_con_tipo_4_y_su_revision() -> None:
    fila = fila_siges(t4st_valor=1_500.0, t4st_fecha=date(2026, 4, 25), t4st_para_facturar=True)

    clase = agrupar_por_equipo([fila])[0].clases[0]

    assert clase.t4_mas_reciente == LecturaRef(1_500.0, date(2026, 4, 25), 4)
    assert clase.t4_revisado is True


def test_parque_historico_conserva_n_y_cruda_aunque_el_p80_sea_null() -> None:
    """El "Detalle por Modelo histórico": N<=1 deja el P80 en NULL, pero la
    grilla del legacy igual muestra N y la mediana cruda."""
    fila = fila_siges(
        prom_parque_cliente_modelo=None, pcm_cant=1, pcm_mediana_cruda=900.0,
        prom_parque_global_modelo=1_200.0, pgl_cant=40, pgl_mediana_cruda=1_150.0,
    )

    clase = agrupar_por_equipo([fila])[0].clases[0]

    assert clase.parque_cliente_modelo is None
    assert clase.parque_historico is not None
    cm, gl = clase.parque_historico.cliente_modelo, clase.parque_historico.global_modelo
    assert (cm.n, cm.p80, cm.cruda) == (1, None, 900.0)
    assert (gl.n, gl.p80, gl.cruda) == (40, 1_200.0, 1_150.0)
