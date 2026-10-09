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

    El sector manda sobre `manage` (decisión de Iván, 2026-10-09): un admin con
    sector asignado administra SOLO su sector y no ve gente de otros. Admin de
    toda la empresa es `es_admin_global` (manage sin sector, o superadmin, que
    llega sin sector desde presentation).
    """

    user_id: UUID
    es_admin: bool
    sector_gestionado_id: UUID | None
    empleado_id: UUID | None

    @property
    def es_admin_global(self) -> bool:
        return self.es_admin and self.sector_gestionado_id is None

    @property
    def es_jefe_de_sector(self) -> bool:
        """Acotado a un sector, tenga o no `manage`."""
        return self.sector_gestionado_id is not None

    def administra(self, department_id: UUID | None) -> bool:
        """Tiene privilegios de admin sobre gente de ese sector."""
        if not self.es_admin:
            return False
        return self.es_admin_global or department_id == self.sector_gestionado_id
