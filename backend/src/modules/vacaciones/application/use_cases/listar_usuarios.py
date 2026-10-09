"""Cuentas de la plataforma para los selects de Gestión Humana (jefe de
sector, vínculo empleado↔usuario), acotadas al alcance del actor."""

from src.modules.vacaciones.domain.repositories.empleado_repository import (
    EmpleadoRepository,
    FiltrosEmpleados,
)
from src.modules.vacaciones.domain.repositories.user_directory import UserDirectory, UserInfo
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones


class ListarUsuariosVisibles:
    def __init__(self, usuarios: UserDirectory, empleados: EmpleadoRepository) -> None:
        self._usuarios = usuarios
        self._empleados = empleados

    async def execute(self, actor: ActorVacaciones) -> list[UserInfo]:
        """El admin general ve todas las cuentas activas; el admin con sector
        asignado, solo las vinculadas a gente de su sector (el alta de un
        empleado nuevo vincula la cuenta sola por mail)."""
        activos = await self._usuarios.list_activos()
        if actor.es_admin_global:
            return activos
        del_sector = await self._empleados.list_filtrados(
            FiltrosEmpleados(department_id=actor.sector_gestionado_id)
        )
        vinculados = {e.user_id for e in del_sector if e.user_id is not None}
        return [u for u in activos if u.id in vinculados]
