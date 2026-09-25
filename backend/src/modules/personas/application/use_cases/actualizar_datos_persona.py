import uuid
from dataclasses import dataclass

from src.modules.personas.application.use_cases.consultar_personas import ObtenerPersona
from src.modules.personas.domain.entities.persona import DatosPersona, Persona
from src.modules.personas.domain.errors import CambioDeMailNoPermitidoError, EmailEnUsoError
from src.modules.personas.domain.repositories.cuentas_gateway import CuentasGateway
from src.modules.personas.domain.repositories.fichas_gateway import FichasGateway
from src.modules.personas.domain.repositories.persona_repository import PersonaRepository


@dataclass(frozen=True, slots=True)
class ActualizarDatosDependencies:
    personas: PersonaRepository
    fichas: FichasGateway
    cuentas: CuentasGateway


class ActualizarDatosPersona:
    """Nombre, mail y color se escriben en la ficha y, si la persona tiene cuenta,
    también en la cuenta: una sola fuente de edición (ADR-040)."""

    def __init__(self, deps: ActualizarDatosDependencies) -> None:
        self._deps = deps

    async def execute(
        self, persona_id: uuid.UUID, datos: DatosPersona, *, puede_gestionar_acceso: bool
    ) -> Persona:
        persona = await ObtenerPersona(self._deps.personas).execute(persona_id)
        if datos.email != persona.datos.email:
            await self._validar_cambio_de_mail(persona, datos.email, puede_gestionar_acceso)
        await self._deps.fichas.actualizar_datos(persona.id, datos)
        if persona.acceso is not None:
            await self._deps.cuentas.actualizar_datos(persona.acceso.user_id, datos)
        return await ObtenerPersona(self._deps.personas).execute(persona_id)

    async def _validar_cambio_de_mail(
        self, persona: Persona, email: str, puede_gestionar_acceso: bool
    ) -> None:
        if persona.acceso is not None and not puede_gestionar_acceso:
            raise CambioDeMailNoPermitidoError()
        user_id = persona.acceso.user_id if persona.acceso else None
        if await self._deps.fichas.email_en_uso(email, excepto=persona.id):
            raise EmailEnUsoError(email)
        if await self._deps.cuentas.email_en_uso(email, excepto=user_id):
            raise EmailEnUsoError(email)
