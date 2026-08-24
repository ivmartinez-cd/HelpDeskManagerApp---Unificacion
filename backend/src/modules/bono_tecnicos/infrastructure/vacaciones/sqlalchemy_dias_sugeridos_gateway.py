"""Adapter que cruza el vínculo Empleado↔Siges (módulo `vacaciones`) con las
ausencias del período para sugerir "Días" — dependencia cross-module a
propósito, solo en infrastructure (nunca en domain/application de
bono_tecnicos), mismo criterio que usa `sla`/infrastructure con `prestadores`.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.bono_tecnicos.domain.services.calculador_dias_sugeridos import (
    AusenciaTecnico,
    calcular_dias_sugeridos,
)
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo
from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.repositories.empleado_repository import FiltrosEmpleados
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_ausencia_repository import (
    SqlAlchemyAusenciaRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)

# Confirmado con el usuario (2026-08-24): estos 4 tipos son los únicos que
# significan "no trabajó ese día" para un técnico de calle. GUARDIA,
# HOME_OFFICE y CAMBIO_HORARIO quedan afuera a propósito — son excepciones de
# modalidad/horario, no ausencias (ver docstring de `TipoAusencia.
# CAMBIO_HORARIO`); OTHER es un catch-all sin semántica definida.
_TIPOS_QUE_DESCUENTAN = frozenset(
    {
        TipoAusencia.DESCUENTO_DIA,
        TipoAusencia.BAJA_ENFERMEDAD,
        TipoAusencia.TRAMITE_PERSONAL,
        TipoAusencia.DIA_ESTUDIO,
    }
)


class SqlAlchemyDiasSugeridosGateway:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_dias_sugeridos_por_tecnico(
        self, periodo: Periodo, ids_tecnico: list[int]
    ) -> dict[int, int]:
        if not ids_tecnico:
            return {}
        empleado_por_siges_id = await self._empleados_vinculados(ids_tecnico)
        if not empleado_por_siges_id:
            return {}
        ausencias_por_empleado = await self._ausencias_por_empleado(
            list(empleado_por_siges_id.values()), periodo
        )
        return {
            siges_id: calcular_dias_sugeridos(
                periodo, ausencias_por_empleado.get(empleado.id, [])
            )
            for siges_id, empleado in empleado_por_siges_id.items()
        }

    async def _empleados_vinculados(self, ids_tecnico: list[int]) -> dict[int, Empleado]:
        empleados = await SqlAlchemyEmpleadoRepository(self._session).list_filtrados(
            FiltrosEmpleados()
        )
        return {e.siges_empresa_id: e for e in empleados if e.siges_empresa_id in ids_tecnico}

    async def _ausencias_por_empleado(
        self, empleados: list[Empleado], periodo: Periodo
    ) -> dict[uuid.UUID, list[AusenciaTecnico]]:
        empleado_ids = [e.id for e in empleados]
        repo = SqlAlchemyAusenciaRepository(self._session)
        ausencias = await repo.list_aprobadas_solapadas_de_empleados(
            empleado_ids, periodo.primer_dia, periodo.ultimo_dia
        )
        return _agrupar_por_empleado(ausencias)


def _agrupar_por_empleado(
    ausencias: list[Ausencia],
) -> dict[uuid.UUID, list[AusenciaTecnico]]:
    por_empleado: dict[uuid.UUID, list[AusenciaTecnico]] = {}
    for a in ausencias:
        if a.tipo not in _TIPOS_QUE_DESCUENTAN:
            continue
        por_empleado.setdefault(a.empleado_id, []).append(
            AusenciaTecnico(start_date=a.start_date, end_date=a.end_date, half_day=a.half_day)
        )
    return por_empleado
