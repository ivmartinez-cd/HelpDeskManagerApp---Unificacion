"""Reglas de armado del archivo de exportación a SiGes (REGLAS_DE_NEGOCIO
§12) — funciones puras, replicadas del `CsvExportService.cs` real del
legacy (el brief documenta el contenido pero no el formato exacto de
columnas; el código gana en ese punto). Formato: una fila por equipo (no por
clase), separador ";", sin comillas RFC 4180, Windows-1252 sin BOM."""

from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
)

ENCABEZADO_CSV = "SERIE;FECHA;TIPO;CLASE_1;CONTADOR_1;CLASE_2;CONTADOR_2;MOTIVO;OBSERVACION"

_MOTIVO_POR_FUENTE: dict[FuenteEstimacion, str] = {
    "Historia_Propia": "14",
    "T4_ST": "14",
    "Backup_SinST": "14",
    "Backup_ConST": "14",
    "EnTransito": "14",
    "Parque_Cliente_Tec": "19",
    "Parque_Cliente_Modelo": "19",
    "Parque_Grupo_Modelo": "19",
    "Parque_Global_Modelo": "19",
}


def motivo_de_fuente(fuente: FuenteEstimacion) -> str:
    """14 = datos del propio equipo, 19 = promedio de parque, vacío =
    pendiente o real (Sin_Estimar) — el operador completa a mano en el ERP."""
    return _MOTIVO_POR_FUENTE.get(fuente, "")


def tipo_toma_export(tipo_toma: int | None) -> str:
    """Guarda dura de grabado (REGLAS_DE_NEGOCIO §4): el export nunca emite
    un tipo de toma "real" — cualquier valor que no sea 14/19 se fuerza a
    14, última línea de defensa por si una regresión futura del motor deja
    pasar otra cosa."""
    if tipo_toma is None:
        return ""
    if tipo_toma == 19:
        return "19"
    return "14"


def escape_csv(value: str | None) -> str:
    """Sin comillas RFC 4180 — no está confirmado que el importador de SiGes
    las interprete. En su lugar, ";" se reemplaza por "," y los saltos de
    línea por espacio (reemplazos 1:1, no alteran el largo presupuestado por
    `armar_resumen_observacion`)."""
    if not value:
        return ""
    return value.replace("\r\n", " ").replace("\n", " ").replace("\r", " ").replace(";", ",")


def sanitizar_simbolos(texto: str) -> str:
    """Caracteres Unicode que no existen en cp1252 (Windows-1252, la
    codepage del importador) reemplazados por equivalentes ASCII — aplicar a
    la observación MANUAL antes de armar el resumen (no después), para que el
    presupuesto de caracteres de `armar_resumen_observacion` se calcule
    sobre el largo definitivo. NO es longitud-neutral ("⚠" → "(!)" suma 2)."""
    return (
        texto.replace("Δ", "")
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("⚠", "(!)")
    )
