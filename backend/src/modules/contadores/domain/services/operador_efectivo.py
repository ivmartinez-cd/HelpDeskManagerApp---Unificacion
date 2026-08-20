# Re-export de las funciones genéricas de resolución (ver ADR-013,
# actualización "tercer módulo") -- contadores no tiene reglas propias, solo
# usa las funciones compartidas con sus tipos concretos (str, str).
from src.shared.domain.services.asignacion_override_resolver import (
    resolver_operador_efectivo as resolver_operador_efectivo,
)
from src.shared.domain.services.asignacion_override_resolver import (
    resolver_override_aplicable as resolver_override_aplicable,
)
