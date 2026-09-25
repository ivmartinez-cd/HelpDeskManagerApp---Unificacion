import json

from src.modules.reporte_incidentes.domain.entities.categoria import (
    Categoria,
    TipificacionGuardada,
)
from src.modules.reporte_incidentes.domain.services.prompt_tipificacion import (
    a_ascii,
    ajustar_a_taxonomia,
    armar_prompt,
    interpretar_respuesta,
    renderizar_caso,
)
from src.modules.reporte_incidentes.domain.services.reglas_prompt import REGLAS_V1
from src.modules.reporte_incidentes.domain.services.tipificacion import PENDIENTE

TAXONOMIA = [
    Categoria("Medio de Impresion", "#f0a400", "papel", ("Atasco de papel (comun)",)),
    Categoria("Software, Firmware y Red", "#7b61ff", "red", ("Driver / PC / Spooler",)),
]


def test_a_ascii_saca_acentos_y_colapsa_espacios() -> None:
    assert a_ascii("  Impresión   dañada ñ ") == "Impresion danada n"


def test_renderiza_el_caso_sin_la_causa() -> None:
    assert renderizar_caso(0, "no imprime", " cambio driver ") == (
        "0. Reporte del cliente: no imprime | Solucion/trabajo del tecnico: cambio driver"
    )
    assert renderizar_caso(3, "atasco", None) == "3. Reporte del cliente: atasco"


def test_el_prompt_lleva_taxonomia_reglas_y_casos() -> None:
    texto = armar_prompt(TAXONOMIA, ["0. Reporte del cliente: x"])
    assert "- Medio de Impresion:\n    * Atasco de papel (comun)" in texto
    assert REGLAS_V1 in texto
    assert texto.endswith("en el mismo orden):\n0. Reporte del cliente: x")


def test_ajusta_a_la_taxonomia_sin_acentos_ni_mayusculas() -> None:
    assert ajustar_a_taxonomia("medio de impresión", "ATASCO DE PAPEL (COMUN)", TAXONOMIA) == (
        "Medio de Impresion", "Atasco de papel (comun)",
    )


def test_subcategoria_desconocida_va_a_otros_y_categoria_desconocida_a_pendiente() -> None:
    assert ajustar_a_taxonomia("Medio de Impresion", "Inventada", TAXONOMIA) == (
        "Medio de Impresion", "Otros - Medio de Impresion",
    )
    assert ajustar_a_taxonomia("Otra cosa", "x", TAXONOMIA) == (PENDIENTE, "")


def test_categoria_que_contiene_el_nombre_tambien_ajusta() -> None:
    assert ajustar_a_taxonomia("Categoria: Medio de Impresion", "x", TAXONOMIA)[0] == (
        "Medio de Impresion"
    )


def test_interpreta_la_respuesta_por_indice_y_completa_lo_que_falta() -> None:
    texto = json.dumps([
        {"i": 1, "categoria": "Software, Firmware y Red",
         "subcategoria": "Driver / PC / Spooler", "confianza": "ALTA"},
        {"i": 9, "categoria": "Medio de Impresion", "subcategoria": "x", "confianza": "alta"},
    ])
    r = interpretar_respuesta(texto, 2, TAXONOMIA)
    assert r[0] == TipificacionGuardada(PENDIENTE, "", "baja")
    assert r[1] == TipificacionGuardada("Software, Firmware y Red", "Driver / PC / Spooler", "alta")


def test_respuesta_no_json_deja_todo_pendiente() -> None:
    assert {t.categoria for t in interpretar_respuesta("no-json", 3, TAXONOMIA)} == {PENDIENTE}


def test_confianza_ausente_vale_media() -> None:
    texto = json.dumps([{"i": 0, "categoria": "Medio de Impresion", "subcategoria": "x"}])
    assert interpretar_respuesta(texto, 1, TAXONOMIA)[0].confianza == "media"
