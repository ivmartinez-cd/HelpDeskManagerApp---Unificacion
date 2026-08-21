from pydantic import BaseModel


class Page[T](BaseModel):
    """Envelope de paginación genérico (ARCHITECTURE_GUIDE.md §11, regla 3:
    "Paginación obligatoria en todo endpoint que retorne colecciones").
    No duplicar este shape por módulo."""

    items: list[T]
    total: int
    page: int
    size: int

    @classmethod
    def of(cls, all_items: list[T], *, page: int, size: int) -> "Page[T]":
        start = (page - 1) * size
        end = start + size
        return cls(items=all_items[start:end], total=len(all_items), page=page, size=size)
