"""Adjuntar/reemplazar el certificado (orden médica, etc.) de una `Ausencia`
ya cargada. Mismo criterio de permiso que editarla (`verificar_puede_modificar_
ausencia`): dueño o admin."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.vacaciones.domain.entities.ausencia import Ausencia
from src.modules.vacaciones.domain.entities.registro_auditoria import (
    ACCION_UPDATE,
    ENTIDAD_AUSENCIA,
)
from src.modules.vacaciones.domain.errors import AusenciaNoEncontradaError
from src.modules.vacaciones.domain.repositories.auditoria import (
    RegistradorAuditoria,
    RegistradorAuditoriaNulo,
)
from src.modules.vacaciones.domain.repositories.ausencia_repository import (
    AusenciaRepository,
)
from src.modules.vacaciones.domain.services.reglas_ausencia import (
    verificar_puede_modificar_ausencia,
)
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones


@dataclass(frozen=True, slots=True)
class AdjuntarCertificadoAusenciaDependencies:
    ausencias: AusenciaRepository
    auditoria: RegistradorAuditoria = RegistradorAuditoriaNulo()


class AdjuntarCertificadoAusencia:
    def __init__(self, deps: AdjuntarCertificadoAusenciaDependencies) -> None:
        self._deps = deps

    async def execute(
        self, ausencia_id: UUID, filename: str, actor: ActorVacaciones
    ) -> Ausencia:
        ausencia = await self._deps.ausencias.get_by_id(ausencia_id)
        if ausencia is None:
            raise AusenciaNoEncontradaError(ausencia_id)
        verificar_puede_modificar_ausencia(actor, ausencia, accion="adjuntar el certificado de")
        ausencia.certificado_filename = filename
        await self._deps.ausencias.save(ausencia)
        await self._deps.auditoria.registrar(
            ACCION_UPDATE,
            ENTIDAD_AUSENCIA,
            str(ausencia.id),
            {"certificado_filename": filename},
        )
        return ausencia
