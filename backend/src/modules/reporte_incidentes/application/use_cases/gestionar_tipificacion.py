"""Corrección manual de una tipificación y ABM de la taxonomía (port de
`resolveClassificationAction` y `categoryActions.ts`)."""

import re
from dataclasses import dataclass

from src.modules.reporte_incidentes.domain.entities.categoria import (
    Categoria,
    TipificacionGuardada,
)
from src.modules.reporte_incidentes.domain.errors import (
    CategoriaInvalidaError,
    CategoriaNoEncontradaError,
    TipificacionInvalidaError,
)
from src.modules.reporte_incidentes.domain.repositories.tipificacion_repositories import (
    TaxonomiaRepository,
    TipificacionCacheRepository,
)
from src.modules.reporte_incidentes.domain.services.tipificacion import CONFIANZA_ALTA, clave_de

_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True, slots=True)
class Correccion:
    """El caso se identifica por su contenido, como la clave de la caché."""

    descripcion: str
    causa: str | None
    solucion: str | None
    categoria: str
    subcategoria: str


class CorregirTipificacion:
    def __init__(
        self, taxonomia: TaxonomiaRepository, cache: TipificacionCacheRepository
    ) -> None:
        self._taxonomia = taxonomia
        self._cache = cache

    async def execute(self, correccion: Correccion) -> None:
        categorias = {c.nombre: c for c in await self._taxonomia.listar()}
        categoria = categorias.get(correccion.categoria)
        if categoria is None:
            raise TipificacionInvalidaError("Categoría inválida")
        if correccion.subcategoria not in categoria.subcategorias:
            raise TipificacionInvalidaError("Subcategoría inválida")
        clave = clave_de(correccion.descripcion, correccion.causa, correccion.solucion)
        guardada = TipificacionGuardada(categoria.nombre, correccion.subcategoria, CONFIANZA_ALTA)
        await self._cache.guardar({clave: guardada})


def _normalizar(categoria: Categoria) -> Categoria:
    subcategorias = tuple(dict.fromkeys(s.strip() for s in categoria.subcategorias if s.strip()))
    return Categoria(
        categoria.nombre.strip(), categoria.color.strip(),
        categoria.descripcion.strip(), subcategorias,
    )


def _validar(categoria: Categoria) -> None:
    if not categoria.nombre:
        raise CategoriaInvalidaError("El nombre de la categoría es obligatorio.")
    if not categoria.descripcion:
        raise CategoriaInvalidaError("La descripción para la guía de IA es obligatoria.")
    if not _COLOR.match(categoria.color):
        raise CategoriaInvalidaError("El color tiene que ser hexadecimal, p. ej. #0275d8.")


def _existe(categorias: list[Categoria], nombre: str) -> bool:
    return any(c.nombre.lower() == nombre.lower() for c in categorias)


class GuardarCategoria:
    """Alta (sin `nombre_anterior`) o edición. Nombre único sin distinguir mayúsculas."""

    def __init__(self, taxonomia: TaxonomiaRepository) -> None:
        self._taxonomia = taxonomia

    async def execute(self, categoria: Categoria, nombre_anterior: str | None) -> None:
        categoria = _normalizar(categoria)
        _validar(categoria)
        actuales = await self._taxonomia.listar()
        if nombre_anterior is not None and not _existe(actuales, nombre_anterior):
            raise CategoriaNoEncontradaError(nombre_anterior)
        cambia_nombre = (nombre_anterior or "").lower() != categoria.nombre.lower()
        if cambia_nombre and _existe(actuales, categoria.nombre):
            raise CategoriaInvalidaError(f'Ya existe una categoría llamada "{categoria.nombre}".')
        if nombre_anterior is None:
            await self._taxonomia.crear(categoria)
        else:
            await self._taxonomia.reemplazar(nombre_anterior, categoria)


class EliminarCategoria:
    def __init__(self, taxonomia: TaxonomiaRepository) -> None:
        self._taxonomia = taxonomia

    async def execute(self, nombre: str) -> None:
        if not _existe(await self._taxonomia.listar(), nombre):
            raise CategoriaNoEncontradaError(nombre)
        await self._taxonomia.eliminar(nombre)
