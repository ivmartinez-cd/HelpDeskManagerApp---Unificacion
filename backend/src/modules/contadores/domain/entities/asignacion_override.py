from src.shared.domain.value_objects.asignacion_override import (
    AsignacionOverride as _SharedAsignacionOverride,
)

# Alias concreto del value object compartido (ver ADR-013 y su actualización
# "tercer módulo" -- turnos se sumó con el mismo patrón, la clase se extrajo
# a shared). En contadores el operador es un username de Gestión y el
# alcance es el nombre de cliente (texto libre, sin catálogo) -- ambos str.
AsignacionOverride = _SharedAsignacionOverride[str, str]
