from dataclasses import dataclass, field

from src.modules.contadores.domain.services.estimacion.observacion_estadisticos import (
    contexto_antiguedad,
    estadisticos_base,
)
from src.modules.contadores.domain.services.estimacion.observacion_etiquetas import (
    avisos,
    etiqueta_metodo,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)

LIMITE_CARACTERES_DEFAULT = 200


@dataclass(frozen=True, slots=True)
class DatosObservacion:
    """Insumos para armar la observación de UN equipo (REGLAS_DE_NEGOCIO
    §12). `resultados` ya viene armado por el caller con las clases que de
    verdad necesitan describirse — clave "" cuando el equipo tiene un solo
    contador, "Mono"/"Color" cuando discrimina (§9)."""

    resultados: dict[str, EstimacionResultado]
    entrada: EstimacionInput
    texto_operador: str | None = field(default=None)
    id_auditoria: str | None = field(default=None)
    forzado_por_operador: bool = field(default=False)


def armar_resumen_observacion(
    datos: DatosObservacion, limite: int = LIMITE_CARACTERES_DEFAULT
) -> str:
    """Formato de LEYENDA_OBSERVACION.md: texto del operador | método |
    impresiones | estadísticos | #IdLog. Si no entra todo, se sacrifican
    bloques en orden de prioridad (REGLAS_DE_NEGOCIO §12 punto 3) — el
    método nunca se sacrifica, el texto del operador tampoco."""
    piezas = _piezas(datos)
    incluir = {"contexto": True, "estadisticos": True, "impresiones": True, "idlog": True}
    texto = _construir(piezas, incluir)
    for clave in ("contexto", "estadisticos", "impresiones", "idlog"):
        if len(texto) <= limite:
            break
        incluir[clave] = False
        texto = _construir(piezas, incluir)
    return texto


@dataclass(frozen=True, slots=True)
class _Piezas:
    texto_operador: str
    metodo: str
    impresiones: str
    estadisticos: str
    contexto: str
    idlog: str


def _piezas(datos: DatosObservacion) -> _Piezas:
    idlog = f"#{datos.id_auditoria}" if datos.id_auditoria else ""
    return _Piezas(
        texto_operador=datos.texto_operador or "",
        metodo=_bloque_metodo(datos.resultados, datos.forzado_por_operador),
        impresiones=_segmento_impresiones(datos.resultados),
        estadisticos=estadisticos_base(datos.resultados, datos.entrada),
        contexto=contexto_antiguedad(datos.resultados, datos.entrada),
        idlog=idlog,
    )


def _construir(piezas: _Piezas, incluir: dict[str, bool]) -> str:
    stats = [piezas.estadisticos] if incluir["estadisticos"] else []
    if incluir["contexto"] and piezas.contexto:
        stats.append(piezas.contexto)
    segmentos = [piezas.texto_operador, piezas.metodo]
    if incluir["impresiones"]:
        segmentos.append(piezas.impresiones)
    segmentos.append(" | ".join(s for s in stats if s))
    if incluir["idlog"]:
        segmentos.append(piezas.idlog)
    return " | ".join(s for s in segmentos if s)


def _bloque_metodo(resultados: dict[str, EstimacionResultado], forzado: bool) -> str:
    textos = {clave: _texto_metodo_avisos(r, forzado) for clave, r in resultados.items()}
    if len(textos) == 1:
        return next(iter(textos.values()))
    if len(set(textos.values())) == 1:
        return f"M+C:{next(iter(textos.values()))}"
    orden = [c for c in ("Mono", "Color") if c in textos]
    return " / ".join(f"{c[0]}:{textos[c]}" for c in orden)


def _texto_metodo_avisos(r: EstimacionResultado, forzado: bool) -> str:
    return ", ".join([etiqueta_metodo(r), *avisos(r, forzado)])


def _segmento_impresiones(resultados: dict[str, EstimacionResultado]) -> str:
    return " ".join(
        f"{clave} {_formatear_impresion(r.impresiones)}".strip()
        for clave, r in resultados.items()
    )


def _formatear_impresion(valor: float | None) -> str:
    entero = round(valor) if valor is not None else 0
    return f"+{entero}" if entero >= 0 else str(entero)
