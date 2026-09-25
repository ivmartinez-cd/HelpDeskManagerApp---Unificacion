"""Prompt de tipificación y lectura de la respuesta de la IA (port de `classify.ts`).

Textos literales del legacy: la caché importada se generó con este prompt, y
cambiarlo cambia las tipificaciones. Sin few-shot: el legacy lo leía de un
archivo que no existe en el repo, así que nunca mandaba ejemplos."""

import json
import re
import unicodedata

from src.modules.reporte_incidentes.domain.entities.categoria import (
    Categoria,
    TipificacionGuardada,
)
from src.modules.reporte_incidentes.domain.services.reglas_prompt import REGLAS_V1
from src.modules.reporte_incidentes.domain.services.tipificacion import PENDIENTE

_CONFIANZA = (
    "CONFIANZA: devolve 'confianza'='alta' si el caso encaja sin ambiguedad en una sola "
    "(categoria, subcategoria); 'media' si es razonable pero hay duda; 'baja' si es "
    "genuinamente ambiguo o quedo sin resolver. Se honesto: preferimos 'baja' (va a revision "
    "humana) antes que una etiqueta dudosa con falsa seguridad."
)
_DETERMINISMO = (
    "DETERMINISMO: para el mismo caso, elegi siempre la misma clasificacion. Segui las "
    "reglas de forma literal y mecanica, sin variar la respuesta entre corridas."
)
_ASCII = "SIN ACENTOS: responde en ASCII puro, copiando los nombres EXACTOS de la lista."
_ROL = (
    "Sos un experto en soporte tecnico de impresion. Clasifica cada incidente en UNA "
    "(categoria, subcategoria) EXACTA de esta taxonomia CERRADA (no inventes ninguna):"
)
_PEDIDO = (
    "CASOS A CLASIFICAR (responde SOLO un arreglo JSON [{i, categoria, subcategoria, "
    "confianza}] en el mismo orden):"
)
SIN_TIPIFICAR = TipificacionGuardada(PENDIENTE, "", "baja")


def a_ascii(texto: str) -> str:
    """ASCII sin acentos ni artefactos de codificación, espacios colapsados."""
    sin_marcas = unicodedata.normalize("NFD", texto or "")
    sin_marcas = re.sub(r"[\u0300-\u036f]", "", sin_marcas)
    sin_marcas = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", sin_marcas)
    sin_marcas = re.sub(r"[^\x00-\x7f]", "", sin_marcas)
    return re.sub(r"\s+", " ", sin_marcas).strip()


def _norm(texto: str) -> str:
    return a_ascii(texto).lower()


def _texto_taxonomia(categorias: list[Categoria]) -> str:
    return "\n".join(
        f"- {c.nombre}:\n    " + "\n    ".join(f"* {s}" for s in c.subcategorias)
        for c in categorias
    )


def introduccion(categorias: list[Categoria]) -> str:
    return (
        f"{_ROL}\n\n{_texto_taxonomia(categorias)}\n\nREGLAS:\n{REGLAS_V1}"
        f"\n\n{_CONFIANZA}\n\n{_DETERMINISMO}\n\n{_ASCII}"
    )


def renderizar_caso(indice: int, descripcion: str, solucion: str | None) -> str:
    """La causa NO se manda (regla 3: es ruido)."""
    partes = [f"{indice}. Reporte del cliente: {descripcion}"]
    if solucion and solucion.strip():
        partes.append(f"Solucion/trabajo del tecnico: {solucion.strip()}")
    return " | ".join(partes)


def armar_prompt(categorias: list[Categoria], casos: list[str]) -> str:
    """`casos` ya renderizados con `renderizar_caso`, en orden de índice."""
    return f"{introduccion(categorias)}\n\n{_PEDIDO}\n" + "\n".join(casos)


def ajustar_a_taxonomia(
    categoria: str, subcategoria: str, categorias: list[Categoria]
) -> tuple[str, str]:
    """Nombres canónicos; categoría desconocida => Pendiente, subcategoría
    desconocida => "Otros - <categoria>"."""
    buscada = _norm(categoria)
    cat = next(
        (c for c in categorias if _norm(c.nombre) == buscada or _norm(c.nombre) in buscada),
        None,
    )
    if cat is None:
        return PENDIENTE, ""
    sub = next((s for s in cat.subcategorias if _norm(s) == _norm(subcategoria)), None)
    return cat.nombre, sub or f"Otros - {cat.nombre}"


def _item(crudo: dict[str, object], categorias: list[Categoria]) -> TipificacionGuardada:
    categoria, subcategoria = ajustar_a_taxonomia(
        str(crudo.get("categoria") or ""), a_ascii(str(crudo.get("subcategoria") or "")), categorias
    )
    confianza = str(crudo.get("confianza") or "media").lower()
    return TipificacionGuardada(categoria, subcategoria, confianza)


def interpretar_respuesta(
    texto: str, esperados: int, categorias: list[Categoria]
) -> list[TipificacionGuardada]:
    """Una tipificación por caso, en orden; lo que falte o no parsee queda Pendiente."""
    salida = [SIN_TIPIFICAR] * esperados
    try:
        items = json.loads(texto)
    except ValueError:
        return salida
    for crudo in items if isinstance(items, list) else []:
        indice = crudo.get("i") if isinstance(crudo, dict) else None
        if isinstance(indice, int) and 0 <= indice < esperados:
            salida[indice] = _item(crudo, categorias)
    return salida
