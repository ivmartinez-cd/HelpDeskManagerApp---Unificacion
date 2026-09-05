"""Casos derivados literalmente de los ejemplos de LEYENDA_OBSERVACION.md
(formato, método, avisos, estadísticos, degradación por prioridad)."""

from datetime import date

from src.modules.contadores.domain.services.estimacion.resumen_observacion import (
    DatosObservacion,
    armar_resumen_observacion,
)
from tests.unit.domain.contadores.estimacion._builders import lectura, make_input, parque
from tests.unit.domain.contadores.estimacion._resultado_builder import make_resultado


def test_formato_parque_con_contexto_de_antiguedad() -> None:
    resultados = {
        "Mono": make_resultado(fuente="Parque_Cliente_Modelo", tipo_toma=19, impresiones=146),
        "Color": make_resultado(fuente="Parque_Cliente_Modelo", tipo_toma=19, impresiones=38),
    }
    entrada = make_input(
        ultimo_real=lectura(0, date(2026, 1, 30)),
        parque_cliente_modelo=parque(0, n_equipos=14, n_descartados=2),
    )

    texto = armar_resumen_observacion(DatosObservacion(resultados, entrada))

    assert texto == "M+C:Parque cli/mod | Mono +146 Color +38 | P80 14eq(-2 desc) | sin real 3m"


def test_t4_tal_cual_sin_par_pl() -> None:
    resultados = {
        "Mono": make_resultado(
            fuente="T4_ST", metodo_detalle="T4ST valor", nota_operador="algo", impresiones=512
        ),
        "Color": make_resultado(
            fuente="T4_ST", metodo_detalle="T4ST valor", nota_operador="algo", impresiones=90
        ),
    }
    entrada = make_input()

    texto = armar_resumen_observacion(DatosObservacion(resultados, entrada))

    assert texto == "M+C:T4 ST tal cual, sin par P/L | Mono +512 Color +90"


def test_metodos_distintos_por_clase_con_estadisticos_de_entre_reales() -> None:
    resultados = {
        "Mono": make_resultado(
            fuente="Historia_Propia",
            metodo_detalle="Entre dos reales",
            impresiones=211,
            dias_par_pl=62,
            tasa_diaria=3.4,
            dias_proyectados=28,
        ),
        "Color": make_resultado(fuente="Parque_Cliente_Modelo", tipo_toma=19, impresiones=47),
    }
    entrada = make_input()

    texto = armar_resumen_observacion(DatosObservacion(resultados, entrada))

    assert texto == (
        "M:Entre reales / C:Parque cli/mod | Mono +211 Color +47 | 62d 3,4/dia extrap +28d"
    )


def test_texto_del_operador_nunca_se_pierde_y_va_primero() -> None:
    resultados = {
        "Mono": make_resultado(fuente="Parque_Grupo_Modelo", tipo_toma=19, impresiones=1204),
        "Color": make_resultado(fuente="Parque_Grupo_Modelo", tipo_toma=19, impresiones=310),
    }
    entrada = make_input()
    datos = DatosObservacion(
        resultados,
        entrada,
        texto_operador="Cliente confirmo mudanza de sede el 12/07, sin uso todo el periodo",
        id_auditoria="48213",
    )

    texto = armar_resumen_observacion(datos)

    assert texto == (
        "Cliente confirmo mudanza de sede el 12/07, sin uso todo el periodo "
        "| M+C:Parque grupo/mod | Mono +1204 Color +310 | #48213"
    )


def test_una_sola_clase_no_lleva_prefijo() -> None:
    resultados = {"": make_resultado(fuente="Historia_Propia", impresiones=100)}
    entrada = make_input()

    texto = armar_resumen_observacion(DatosObservacion(resultados, entrada))

    assert texto == "Entre reales | +100"


def test_degradacion_por_prioridad_conserva_texto_y_metodo_primero() -> None:
    resultados = {
        "Mono": make_resultado(
            fuente="Parque_Cliente_Modelo",
            tipo_toma=19,
            impresiones=146,
            ajustado_por_receso=True,
        ),
    }
    entrada = make_input(
        ultimo_real=lectura(0, date(2026, 1, 30)),
        parque_cliente_modelo=parque(0, n_equipos=14, n_descartados=2),
    )
    datos = DatosObservacion(resultados, entrada, id_auditoria="99999")

    texto_completo = armar_resumen_observacion(datos)
    texto_recortado = armar_resumen_observacion(datos, limite=40)

    assert "sin real 3m" in texto_completo
    assert "#99999" in texto_completo
    assert len(texto_recortado) <= 40
    assert texto_recortado.startswith("Parque cli/mod, receso")
    assert "sin real 3m" not in texto_recortado
