"""Acciones del módulo `turnos`, sembradas en el catálogo de permisos (ADR-029).

Hasta esa ADR los endpoints de turnos se protegían con `admin.manage` prestado
de auth, así que dar acceso a la grilla obligaba a dar acceso a usuarios y
permisos. Dos acciones alcanzan: `view` (consultar casillas/franjas/coberturas/
grillas de vacaciones) y `manage` (toda mutación: casillas, franjas,
asignaciones, coberturas, intercambios, grillas de vacaciones). Las coberturas
de turnos no tienen módulo propio: son `turnos.manage`, igual que las de
contadores son `contadores.manage` y las de prestadores `prestadores.update`.

`GET /api/turnos/current` (la card de Inicio) sigue siendo solo-sesión a
propósito: cada operador ve el turno del día sin necesitar el módulo."""

from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

_MODULE = ModuleKey("turnos")

VIEW = Permission(_MODULE, ActionKey("view"))
MANAGE = Permission(_MODULE, ActionKey("manage"))
