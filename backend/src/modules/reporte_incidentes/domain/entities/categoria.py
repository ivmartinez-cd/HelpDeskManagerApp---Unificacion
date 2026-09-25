from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Categoria:
    """Categoría de la taxonomía de tipificación, con sus subcategorías en orden.

    `descripcion` es la "Pauta e instrucciones para la IA" que se carga en la
    configuración; el legacy la exige pero hoy NO la manda al modelo."""

    nombre: str
    color: str
    descripcion: str
    subcategorias: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TipificacionGuardada:
    """Tipificación cruda guardada en caché (respuesta de la IA o corrección
    manual). El umbral de confianza se aplica al leerla, no al guardarla."""

    categoria: str
    subcategoria: str
    confianza: str
