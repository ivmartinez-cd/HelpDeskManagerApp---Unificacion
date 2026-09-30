import uuid
from dataclasses import dataclass

from src.modules.personas.application.use_cases.consultar_personas import ObtenerPersona
from src.modules.personas.domain.entities.persona import Persona
from src.modules.personas.domain.errors import (
    CuentaPrivilegiadaError,
    EmailEnUsoError,
    PersonaInactivaError,
)
from src.modules.personas.domain.repositories.cuentas_gateway import (
    AvisoActivacion,
    CuentasGateway,
)
from src.modules.personas.domain.repositories.fichas_gateway import FichasGateway
from src.modules.personas.domain.repositories.persona_repository import PersonaRepository


async def verificar_puede_tocar_cuenta(
    cuentas: CuentasGateway, user_id: uuid.UUID, *, actor_es_superadmin: bool
) -> None:
    """Mail y acceso de una cuenta privilegiada: solo un superadmin."""
    if not actor_es_superadmin and await cuentas.es_privilegiada(user_id):
        raise CuentaPrivilegiadaError()


@dataclass(frozen=True, slots=True)
class AccesoDependencies:
    personas: PersonaRepository
    fichas: FichasGateway
    cuentas: CuentasGateway
    aviso: AvisoActivacion


class DarAcceso:
    """Sin cuenta: la crea con los datos de la persona, la vincula y le manda el
    link para elegir contraseña. Con cuenta desactivada: la reactiva (su
    contraseña sigue siendo la de antes). Toda cuenta nace de una ficha."""

    def __init__(self, deps: AccesoDependencies) -> None:
        self._deps = deps

    async def execute(self, persona_id: uuid.UUID, *, actor_es_superadmin: bool) -> Persona:
        persona = await ObtenerPersona(self._deps.personas).execute(persona_id)
        if not persona.activa:
            raise PersonaInactivaError()
        if persona.acceso is None:
            await self._crear_cuenta(persona)
        elif not persona.acceso.activo:
            user_id = persona.acceso.user_id
            await verificar_puede_tocar_cuenta(
                self._deps.cuentas, user_id, actor_es_superadmin=actor_es_superadmin
            )
            await self._deps.cuentas.activar(user_id)
        return await ObtenerPersona(self._deps.personas).execute(persona_id)

    async def _crear_cuenta(self, persona: Persona) -> None:
        if await self._deps.cuentas.email_en_uso(persona.datos.email, excepto=None):
            raise EmailEnUsoError(persona.datos.email)
        user_id = await self._deps.cuentas.crear(persona.datos)
        await self._deps.fichas.vincular_cuenta(persona.id, user_id)
        await self._deps.aviso.enviar(persona.datos.email)


class QuitarAcceso:
    """Desactiva la cuenta sin desvincularla: conserva su historial y se puede
    volver a dar acceso. Idempotente."""

    def __init__(self, personas: PersonaRepository, cuentas: CuentasGateway) -> None:
        self._personas = personas
        self._cuentas = cuentas

    async def execute(self, persona_id: uuid.UUID, *, actor_es_superadmin: bool) -> Persona:
        persona = await ObtenerPersona(self._personas).execute(persona_id)
        if persona.acceso is not None and persona.acceso.activo:
            user_id = persona.acceso.user_id
            await verificar_puede_tocar_cuenta(
                self._cuentas, user_id, actor_es_superadmin=actor_es_superadmin
            )
            await self._cuentas.desactivar(user_id)
        return await ObtenerPersona(self._personas).execute(persona_id)
