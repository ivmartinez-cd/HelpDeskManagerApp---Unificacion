"""Archivo de exportación a SiGes — `CsvExportService` del Estimador de
Contadores v1.7, funciones puras.

Una fila por máquina (no por clase), separador ";" (separador de listas de
Windows es-AR: con "," el importador de SiGes no separa los campos), sin
comillas RFC 4180 (";" y saltos de línea del texto se sanean), Windows-1252
sin BOM (lo codifica quien sirve el archivo).

CLASE_1/CONTADOR_1 llevan SIEMPRE el contador principal (Cl.10, o Cl.20 si la
máquina no tiene Cl.10); CLASE_2/CONTADOR_2 solo el Color de una máquina que
discrimina. CONTADOR vacío si la fila no tiene estimado (real o pendiente: el
operador completa en el ERP). MOTIVO es el ID del catálogo de Motivos de
estimación de SiGes, no texto. OBSERVACION la arma `resumen_observacion`."""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from src.modules.contadores.domain.services.estimacion.orden_cultura_es_ar import (
    clave_orden_es_ar,
)
from src.modules.contadores.domain.services.estimacion.resumen_observacion import (
    ClaseObservada,
    armar_resumen_observacion,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
)

ENCABEZADO_CSV = "SERIE;FECHA;TIPO;CLASE_1;CONTADOR_1;CLASE_2;CONTADOR_2;MOTIVO;OBSERVACION"
FIN_DE_LINEA = "\r\n"

# 14 = estimación con datos del propio equipo (historia propia, T4 ST, backup
# y en tránsito); 19 = promedio del parque. Real / pendiente: vacío.
_MOTIVO_POR_FUENTE: dict[FuenteEstimacion, str] = {
    "Historia_Propia": "14",
    "T4_ST": "14",
    "Backup_SinST": "14",
    "EnTransito": "14",
    "Parque_Cliente_Tec": "19",
    "Parque_Cliente_Modelo": "19",
    "Parque_Grupo_Modelo": "19",
    "Parque_Global_Modelo": "19",
}


@dataclass(frozen=True, slots=True)
class FilaExport:
    """Una fila (equipo, clase) efectiva del tablero, con lo que el export lee
    del `EquipoGrilla` del legacy."""

    id_maquina: int
    clase: str
    nro_serie: str
    empresa: str
    sucursal: str
    observada: ClaseObservada


@dataclass(frozen=True, slots=True)
class AuditoriaMaquina:
    """Observación manual más reciente (ya saneada) y `#IdLog` del último
    movimiento de la máquina en el proceso."""

    observacion_manual: str | None = None
    id_log: str | None = None


def motivo_de_fuente(fuente: FuenteEstimacion) -> str:
    return _MOTIVO_POR_FUENTE.get(fuente, "")


def tipo_toma_export(tipo_toma: int | None) -> str:
    """Guarda dura: el Estimador solo graba T14 o T19. Cualquier otro tipo
    que llegue acá (una regresión del cálculo) sale como T14, nunca real."""
    if tipo_toma is None:
        return ""
    return "19" if tipo_toma == 19 else "14"


def contador_export(valor: float | None) -> str:
    """`{x:0}` sobre decimal: entero, el medio lejos del cero."""
    if valor is None:
        return ""
    return str(int(Decimal(repr(valor)).quantize(Decimal(1), rounding=ROUND_HALF_UP)))


def escape_csv(valor: str | None) -> str:
    """Reemplazos 1:1 (no cambian el largo presupuestado de la observación)."""
    if not valor:
        return ""
    return valor.replace("\r\n", " ").replace("\n", " ").replace("\r", " ").replace(";", ",")


def sanitizar_simbolos(texto: str) -> str:
    """Símbolos fuera de cp1252 → ASCII. NO es longitud-neutral ("⚠" → "(!)"):
    se aplica a la observación manual ANTES de armar el resumen."""
    return (
        texto.replace("Δ", "")
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("⚠", "(!)")
    )


def agrupar_por_maquina(filas: list[FilaExport]) -> list[list[FilaExport]]:
    """Agrupa por máquina (en orden de aparición) y ordena como la grilla por
    defecto: empresa, sucursal, nro de serie, con la comparación de cultura
    es-AR del `OrderBy` de .NET (orden estable ante empates)."""
    grupos: dict[int, list[FilaExport]] = {}
    for fila in filas:
        grupos.setdefault(fila.id_maquina, []).append(fila)
    return sorted(grupos.values(), key=_clave_orden)


def linea_csv(
    grupo: list[FilaExport], fecha_objetivo: date, auditoria: AuditoriaMaquina | None
) -> str | None:
    """La línea de una máquina. `None` si no tiene Cl.10 ni Cl.20. TIPO y
    MOTIVO salen del contador principal."""
    cl10 = next((f for f in grupo if f.clase == "10"), None)
    cl20 = next((f for f in grupo if f.clase == "20"), None)
    principal = cl10 if cl10 is not None else cl20
    if principal is None:
        return None
    r1 = principal.observada.resultado
    observacion = _observacion(cl10, cl20, auditoria or AuditoriaMaquina())
    serie_fecha_tipo = [
        escape_csv(principal.nro_serie),
        fecha_objetivo.strftime("%d/%m/%Y"),
        tipo_toma_export(r1.tipo_toma),
    ]
    contadores = [*_clase_y_contador(principal), *_clase_y_contador(cl20 if cl10 else None)]
    return ";".join([*serie_fecha_tipo, *contadores, motivo_de_fuente(r1.fuente), observacion])


def _clase_y_contador(fila: FilaExport | None) -> tuple[str, str]:
    if fila is None:
        return "", ""
    return fila.clase, contador_export(fila.observada.resultado.estim_propuesto)


def _observacion(
    cl10: FilaExport | None, cl20: FilaExport | None, auditoria: AuditoriaMaquina
) -> str:
    return escape_csv(
        armar_resumen_observacion(
            cl10.observada if cl10 is not None else None,
            cl20.observada if cl20 is not None else None,
            auditoria.observacion_manual,
            auditoria.id_log,
        )
    )


def _clave_orden(grupo: list[FilaExport]) -> tuple[tuple[tuple[int, ...], ...], ...]:
    primera = grupo[0]
    textos = (primera.empresa, primera.sucursal, primera.nro_serie)
    return tuple(clave_orden_es_ar(t) for t in textos)
