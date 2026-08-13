from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ActorVacaciones:
    """Identidad del usuario proyectada al vocabulario del módulo (D4 del plan).

    La construye presentation (`get_actor_vacaciones`) a partir de los grants
    de la matriz de permisos + `user_module_scope` + el vínculo
    `vacaciones_empleado.user_id`; domain y application solo ven este dataclass.

    - `es_admin`: tiene la acción `manage` (rol ADMIN del legacy).
    - `sector_gestionado_id`: sector asignado en `user_module_scope` para el
      módulo (rol MANAGER del legacy). None = sin alcance sectorial.
    - `empleado_id`: empleado vinculado a la cuenta (para "lo propio").
    """

    user_id: UUID
    es_admin: bool
    sector_gestionado_id: UUID | None
    empleado_id: UUID | None

    @property
    def es_jefe_de_sector(self) -> bool:
        return not self.es_admin and self.sector_gestionado_id is not None
