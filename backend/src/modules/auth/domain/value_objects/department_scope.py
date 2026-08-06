import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GlobalScope:
    """Sin restricción de sector — ve todo el módulo."""


@dataclass(frozen=True, slots=True)
class SingleDepartment:
    department_id: uuid.UUID


# Unión cerrada, sin variante nula: el bug de VacaSync (`?? undefined` que
# borraba el filtro y fallaba abierto) es literalmente irrepresentable acá.
type DepartmentScope = GlobalScope | SingleDepartment
