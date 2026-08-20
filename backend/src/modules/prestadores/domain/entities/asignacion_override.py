import uuid

from src.shared.domain.value_objects.asignacion_override import (
    AsignacionOverride as _SharedAsignacionOverride,
)

# Alias concreto del value object compartido (ver ADR-013 y su actualización
# "tercer módulo" -- turnos es ese tercer módulo, la clase se extrajo a
# shared). En prestadores tanto el operador (app_user) como el elemento de
# alcance (prestador) son UUID.
AsignacionOverride = _SharedAsignacionOverride[uuid.UUID, uuid.UUID]
