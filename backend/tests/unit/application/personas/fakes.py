import uuid
from dataclasses import replace

from src.modules.personas.domain.entities.persona import AccesoPersona, DatosPersona, Persona
from src.modules.personas.domain.repositories.persona_repository import (
    FiltrosPersonas,
    OrdenPersonas,
)


def make_persona(
    *,
    email: str = "ana@canal.com",
    activa: bool = True,
    acceso: AccesoPersona | None = None,
) -> Persona:
    return Persona(
        id=uuid.uuid4(),
        datos=DatosPersona(first_name="Ana", last_name="Paz", email=email, color="#112233"),
        activa=activa,
        sector_id=uuid.uuid4(),
        sector_nombre="Mesa",
        cargo_nombre="Técnico",
        acceso=acceso,
    )


def make_acceso(*, activo: bool = True) -> AccesoPersona:
    return AccesoPersona(user_id=uuid.uuid4(), activo=activo, superadmin=False, ultimo_ingreso=None)


class Mundo:
    """Fichas y cuentas en memoria, consistentes entre sí: los gateways escriben
    acá y el repositorio lee de acá, como la DB real."""

    def __init__(self, *personas: Persona) -> None:
        self.personas = {p.id: p for p in personas}
        self.cuentas: dict[uuid.UUID, tuple[str, bool, DatosPersona | None]] = {}
        for p in personas:
            if p.acceso:
                self.cuentas[p.acceso.user_id] = (p.datos.email, p.acceso.activo, None)
        self.mails: list[str] = []
        self.privilegiadas: set[uuid.UUID] = set()


class FakePersonaRepository:
    def __init__(self, mundo: Mundo) -> None:
        self._mundo = mundo

    async def list_page(
        self, filtros: FiltrosPersonas, orden: OrdenPersonas, *, page: int, size: int
    ) -> tuple[list[Persona], int]:
        todas = list(self._mundo.personas.values())
        return todas[(page - 1) * size : page * size], len(todas)

    async def get(self, persona_id: uuid.UUID) -> Persona | None:
        return self._mundo.personas.get(persona_id)


class FakeFichas:
    def __init__(self, mundo: Mundo) -> None:
        self._mundo = mundo

    async def email_en_uso(self, email: str, *, excepto: uuid.UUID) -> bool:
        return any(
            p.datos.email == email and p.id != excepto for p in self._mundo.personas.values()
        )

    async def actualizar_datos(self, persona_id: uuid.UUID, datos: DatosPersona) -> None:
        self._mundo.personas[persona_id] = replace(self._mundo.personas[persona_id], datos=datos)

    async def vincular_cuenta(self, persona_id: uuid.UUID, user_id: uuid.UUID) -> None:
        email, activo, _ = self._mundo.cuentas[user_id]
        acceso = AccesoPersona(
            user_id=user_id, activo=activo, superadmin=False, ultimo_ingreso=None
        )
        persona = self._mundo.personas[persona_id]
        self._mundo.personas[persona_id] = replace(persona, acceso=acceso)


class FakeCuentas:
    def __init__(self, mundo: Mundo) -> None:
        self._mundo = mundo

    async def email_en_uso(self, email: str, *, excepto: uuid.UUID | None) -> bool:
        return any(e == email and uid != excepto for uid, (e, _, _) in self._mundo.cuentas.items())

    async def es_privilegiada(self, user_id: uuid.UUID) -> bool:
        return user_id in self._mundo.privilegiadas

    async def actualizar_datos(self, user_id: uuid.UUID, datos: DatosPersona) -> None:
        _, activo, _ = self._mundo.cuentas[user_id]
        self._mundo.cuentas[user_id] = (datos.email, activo, datos)

    async def crear(self, datos: DatosPersona) -> uuid.UUID:
        user_id = uuid.uuid4()
        self._mundo.cuentas[user_id] = (datos.email, True, datos)
        return user_id

    async def activar(self, user_id: uuid.UUID) -> None:
        self._set_activo(user_id, True)

    async def desactivar(self, user_id: uuid.UUID) -> None:
        self._set_activo(user_id, False)

    def _set_activo(self, user_id: uuid.UUID, activo: bool) -> None:
        email, _, datos = self._mundo.cuentas[user_id]
        self._mundo.cuentas[user_id] = (email, activo, datos)
        for pid, p in self._mundo.personas.items():
            if p.acceso and p.acceso.user_id == user_id:
                self._mundo.personas[pid] = replace(p, acceso=replace(p.acceso, activo=activo))


class FakeAviso:
    def __init__(self, mundo: Mundo) -> None:
        self._mundo = mundo

    async def enviar(self, email: str) -> None:
        self._mundo.mails.append(email)
