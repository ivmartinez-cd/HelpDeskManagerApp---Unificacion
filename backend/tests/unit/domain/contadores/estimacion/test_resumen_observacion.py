"""Columna OBSERVACION del CSV — casos portados de `ResumenObservacionTests.cs`
del Estimador de Contadores v1.7. Contrato duro: nunca más de 200 caracteres
(SiGes descarta el registro entero si se pasa); lo demás existe para que el
recorte no se lleve la información útil."""

from itertools import product

from src.modules.contadores.domain.services.estimacion.codificacion_cp1252 import (
    codificar_cp1252,
)
from src.modules.contadores.domain.services.estimacion.resumen_observacion import (
    MAX_OBSERVACION,
    ClaseObservada,
    armar_resumen_observacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    DetalleParque,
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    MarcaEstimacion,
)
from tests.unit.domain.contadores.estimacion._resultado_builder import make_resultado

_MARCAS: tuple[MarcaEstimacion, ...] = (
    "AjustadoPorReceso",
    "UsaT4EnPar",
    "T4SinRevisar",
    "SinParValido",
    "InterpoladoAtras",
    "PLManual",
    "ForzadoPorOperador",
)


def _marcas(bits: int) -> frozenset[MarcaEstimacion]:
    return frozenset(m for i, m in enumerate(_MARCAS) if bits >> i & 1)


def _eq(
    propuesto: float | None, impresiones: float | None, meses: int | None, r: EstimacionResultado
) -> ClaseObservada:
    return ClaseObservada(
        make_resultado(estim_propuesto=propuesto, impresiones=impresiones, **_decision(r)), meses
    )


def _decision(r: EstimacionResultado) -> dict[str, object]:
    return dict(
        fuente=r.fuente,
        metodo=r.metodo,
        marcas=r.marcas,
        detalle_parque=r.detalle_parque,
        dias_par_pl=r.dias_par_pl,
        tasa_diaria=r.tasa_diaria,
        dias_proyectados=r.dias_proyectados,
    )


def _parque(imp: float, n: int, descartados: int, meses: int) -> ClaseObservada:
    decision = make_resultado(
        fuente="Parque_Cliente_Modelo",
        metodo="MedianaTruncadaP80",
        detalle_parque=DetalleParque(n, descartados, True, None, None),
    )
    return _eq(10_000 + imp, imp, meses, decision)


def _entre_reales(imp: float) -> ClaseObservada:
    decision = make_resultado(
        fuente="Historia_Propia",
        metodo="EntreReales",
        dias_par_pl=62,
        tasa_diaria=3.4,
        dias_proyectados=28,
    )
    return _eq(80_000, imp, 0, decision)


# ── Contrato duro: el límite de SiGes ─────────────────────────────────────────


def test_caso_reportado_parque_mono_y_color_entra_en_200() -> None:
    r = armar_resumen_observacion(_parque(146, 14, 2, 3), _parque(38, 12, 1, 3))

    assert len(r) <= MAX_OBSERVACION
    assert r == "M+C:Parque cli/mod | Mono +146 Color +38 | P80 14eq(-2 desc) | sin real 3m"


def test_caso_reportado_t4_sin_par_entra_en_200() -> None:
    d = make_resultado(fuente="T4_ST", metodo="T4ST_Valor", marcas=frozenset({"SinParValido"}))

    r = armar_resumen_observacion(_eq(50_000, 512, None, d), _eq(9_000, 90, None, d))

    assert r == "M+C:T4 ST tal cual, sin par P/L | Mono +512 Color +90"


def test_nunca_supera_200_ni_en_el_peor_caso() -> None:
    """Las 128 combinaciones de marcas, Mono y Color con marcas opuestas (el
    nivel de método más largo), con y sin observación manual desbordada."""
    manuales = [None, "", "Revisado con el tecnico", "N" * 400]
    for bits, manual in product(range(128), manuales):
        d = make_resultado(
            fuente="T4_ST",
            metodo="T4ST_Proyectado",
            detalle_parque=DetalleParque(999_999, 99_999, True, None, None),
            dias_par_pl=9_999,
            tasa_diaria=98_765.43,
            dias_proyectados=999,
            marcas=_marcas(bits),
        )
        otra = make_resultado(**{**_decision(d), "marcas": _marcas(~bits & 127)})

        r = armar_resumen_observacion(
            _eq(1, 987_654, 240, d), _eq(1, -987_654, 240, otra), manual, str(2_147_483_647)
        )

        assert len(r) <= MAX_OBSERVACION, (bits, manual, r)


# ── Factorización ──────────────────────────────────────────────────────────────


def test_mismo_metodo_en_ambas_clases_se_emite_una_sola_vez() -> None:
    r = armar_resumen_observacion(_parque(146, 14, 2, 3), _parque(38, 12, 1, 3))

    assert r.startswith("M+C:")
    assert r.count("Parque cli/mod") == 1


def test_metodos_distintos_se_discriminan_mono_y_color() -> None:
    r = armar_resumen_observacion(_entre_reales(211), _parque(47, 9, 0, 9))

    assert r == (
        "M:Entre reales / C:Parque cli/mod | Mono +211 Color +47 | 62d 3.4/dia extrap +28d"
        " | sin real 9m"
    )


def test_una_sola_clase_no_lleva_prefijo() -> None:
    r = armar_resumen_observacion(_entre_reales(310), None)

    assert r == "Entre reales | +310 imp | 62d 3.4/dia extrap +28d"


# ── Prioridad de recorte ───────────────────────────────────────────────────────


def test_observacion_manual_tiene_prioridad_sobre_el_detalle_automatico() -> None:
    manual = "X" * 150

    r = armar_resumen_observacion(_parque(146, 14, 2, 3), _parque(38, 12, 1, 3), manual)

    assert r.startswith("XXX")
    assert len(r) <= MAX_OBSERVACION
    assert "Parque cli/mod" in r


def test_observacion_manual_corta_devuelve_el_sobrante_al_detalle() -> None:
    r = armar_resumen_observacion(_parque(146, 14, 2, 3), _parque(38, 12, 1, 3), "ok")

    assert r.startswith("ok | ")
    assert "P80 14eq" in r
    assert "sin real 3m" in r


def test_metodo_e_impresiones_sobreviven_al_cupo_mas_apretado() -> None:
    r = armar_resumen_observacion(_entre_reales(211), _parque(47, 9, 0, 9), "N" * 400, "2147483647")

    assert len(r) <= MAX_OBSERVACION
    assert "Mono +211" in r
    assert "Color +47" in r


def test_observacion_manual_larga_se_recorta_con_puntos_suspensivos() -> None:
    r = armar_resumen_observacion(_entre_reales(310), None, "N" * 400)

    detalle = "Entre reales | +310 imp | 62d 3.4/dia extrap +28d"
    assert r == "N" * (200 - len(detalle) - 3 - 3) + "... | " + detalle


# ── Regresiones encontradas en revisión (v1.7) ────────────────────────────────


def test_pl_manual_con_llegada_t4_conserva_los_estadisticos_del_par() -> None:
    d = make_resultado(
        fuente="T4_ST",
        metodo="T4ST_Valor",
        dias_par_pl=62,
        tasa_diaria=3.4,
        dias_proyectados=28,
        marcas=frozenset({"PLManual", "UsaT4EnPar"}),
    )

    r = armar_resumen_observacion(_eq(90_000, 1_234, 0, d), None)

    assert r == "P/L manual, usa T4 | +1234 imp | 62d 3.4/dia extrap +28d"


def test_contexto_del_color_no_se_pierde_cuando_el_mono_tiene_historia_propia() -> None:
    r = armar_resumen_observacion(_entre_reales(211), _parque(47, 9, 0, 7))

    assert "sin real 7m" in r


def test_maquina_que_discrimina_con_una_sola_clase_estimada_lleva_prefijo() -> None:
    """La otra clase ya tenía lectura real: tiene valor pero no decisión."""
    real = ClaseObservada(make_resultado(estim_propuesto=5_000, metodo="NoAplica"))

    r = armar_resumen_observacion(real, _parque(47, 9, 0, 7))

    assert r.startswith("C:")


# ── Marcas, estadísticos y contexto ────────────────────────────────────────────


def test_marcas_en_orden_de_gravedad_y_forzado_por_operador() -> None:
    d = make_resultado(marcas=_marcas(127) - {"PLManual"}, metodo="EntreReales")

    r = armar_resumen_observacion(_eq(1, 5, None, d), None)

    assert r.startswith(
        "Entre reales, (!)T4 sin revisar, sin par P/L, interp. atras, usa T4, receso, forzado op."
    )


def test_mediana_cruda_sin_descartados_y_cero_meses_dice_sin_historia_propia() -> None:
    d = make_resultado(
        fuente="Parque_Global_Modelo",
        metodo="MedianaCruda",
        detalle_parque=DetalleParque(3, 0, False, None, None),
    )

    r = armar_resumen_observacion(_eq(1, 40, 0, d), None)

    assert r == "Parque global/mod | +40 imp | mediana 3eq | sin historia propia"


def test_t4_proyectado_y_backup_y_transito() -> None:
    t4 = make_resultado(fuente="T4_ST", metodo="T4ST_Proyectado")
    backup = make_resultado(fuente="Backup_SinST", metodo="ContadorAnterior")
    transito = make_resultado(fuente="EnTransito", metodo="ContadorAnterior")

    assert armar_resumen_observacion(_eq(1, 7, None, t4), None) == "T4 ST proyectado | +7 imp"
    assert armar_resumen_observacion(_eq(1, 0, None, backup), None) == (
        "Backup sin movimiento | +0 imp"
    )
    assert armar_resumen_observacion(_eq(1, 0, None, transito), None) == (
        "En transito sin movimiento | +0 imp"
    )


def test_par_sin_ceros_y_extrapolacion_negativa() -> None:
    d = make_resultado(metodo="EntreReales", dias_par_pl=0, tasa_diaria=12.5, dias_proyectados=-9)

    assert armar_resumen_observacion(_eq(1, -3, None, d), None) == (
        "Entre reales | -3 imp | 12.5/dia extrap -9d"
    )


# ── Trazabilidad ───────────────────────────────────────────────────────────────


def test_id_log_viaja_al_final() -> None:
    r = armar_resumen_observacion(_parque(146, 14, 2, 3), None, None, "48213")

    assert r.endswith("#48213")


def test_sin_id_log_no_se_emite_numeral() -> None:
    for id_log in (None, ""):
        assert "#" not in armar_resumen_observacion(_parque(146, 14, 2, 3), None, None, id_log)


# ── Bordes ─────────────────────────────────────────────────────────────────────


def test_sin_ninguna_clase_estimada_devuelve_vacio() -> None:
    assert armar_resumen_observacion(None, None) == ""


def test_pendiente_sin_estimado_ni_decision_devuelve_vacio() -> None:
    pendiente = ClaseObservada(make_resultado(estim_propuesto=None, fuente="Pendiente"))

    assert armar_resumen_observacion(pendiente, None) == ""


def test_marcada_pendiente_conserva_el_metodo_pero_sin_valor_no_cuenta() -> None:
    """`ConstruirPendiente` deja la decisión pero borra el estimado."""
    marcada = ClaseObservada(make_resultado(estim_propuesto=None, metodo="EntreReales"))

    assert armar_resumen_observacion(marcada, None, "revisar") == "revisar"


def test_solo_observacion_manual_sin_estimacion_se_conserva() -> None:
    assert armar_resumen_observacion(None, None, "  nota suelta  ") == "nota suelta"


def test_nunca_emite_el_separador_del_csv() -> None:
    fuentes = ["Historia_Propia", "T4_ST", "Backup_SinST", "EnTransito", "Parque_Cliente_Tec"]
    metodos = ["MedianaTruncadaP80", "MedianaCruda", "EntreReales", "T4ST_Proyectado"]
    for fuente, metodo in product(fuentes, metodos):
        d = make_resultado(
            fuente=fuente,
            metodo=metodo,
            detalle_parque=DetalleParque(10, 0, True, None, None),
            dias_par_pl=30,
            tasa_diaria=3.5,
            marcas=_marcas(127),
        )

        r = armar_resumen_observacion(_eq(1000, 100, 3, d), _eq(500, 50, 3, d))

        assert ";" not in r


def test_texto_representable_en_cp1252_un_byte_por_caracter() -> None:
    d = make_resultado(
        fuente="T4_ST",
        metodo="T4ST_Proyectado",
        dias_par_pl=47,
        tasa_diaria=12.75,
        dias_proyectados=-9,
        marcas=_marcas(127),
    )

    r = armar_resumen_observacion(_eq(70_000, 900, 14, d), _eq(9_000, 120, 14, d))

    assert len(codificar_cp1252(r)) == len(r) <= MAX_OBSERVACION


def test_emoji_de_la_observacion_manual_cuenta_doble_como_en_utf16() -> None:
    """El legacy mide en UTF-16: cada emoji ocupa 2 y sale "??" en cp1252."""
    r = armar_resumen_observacion(None, None, "😀" * 120)

    assert codificar_cp1252(r) == b"?" * 197 + b"..."
