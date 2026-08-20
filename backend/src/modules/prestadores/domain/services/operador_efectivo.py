from src.shared.domain.services.asignacion_override_resolver import (
    resolver_operador_efectivo as resolver_operador_efectivo,
)

# Re-export del value object genérico (ver ADR-013, actualización "tercer
# módulo") -- prestadores no tiene reglas propias de resolución, solo usa la
# función compartida con sus tipos concretos (uuid.UUID, uuid.UUID).
