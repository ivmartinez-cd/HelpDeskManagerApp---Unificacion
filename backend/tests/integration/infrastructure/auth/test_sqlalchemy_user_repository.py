import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.repositories.user_repository import CampoOrdenUsuarios
from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.domain.value_objects.password_hash import PasswordHash
from src.modules.auth.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)


def _build_user(email: str = "user@example.com") -> User:
    return User(
        id=uuid.uuid4(),
        email=Email(email),
        password_hash=PasswordHash("$argon2id$fake"),
        full_name="Ada Lovelace",
        is_active=True,
        is_superadmin=False,
        created_at=datetime.now(UTC),
    )


async def test_add_then_get_by_id_round_trips(db_session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository(db_session)
    user = _build_user()

    await repo.add(user)
    found = await repo.get_by_id(user.id)

    assert found is not None
    assert found.email.value == "user@example.com"


async def test_get_by_email_matches_the_normalized_value(db_session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository(db_session)
    await repo.add(_build_user("Person@Example.com"))

    found = await repo.get_by_email(Email("person@example.com"))

    assert found is not None


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository(db_session)

    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_save_persists_changes(db_session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository(db_session)
    user = _build_user()
    await repo.add(user)

    user.is_active = False
    await repo.save(user)

    found = await repo.get_by_id(user.id)
    assert found is not None
    assert found.is_active is False


async def test_list_page_ordena_por_rol_y_estado_segun_la_etiqueta(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyUserRepository(db_session)
    marca = uuid.uuid4().hex[:8]
    datos = [("Beto", False, True), ("Ana", True, False), ("Ciro", False, False)]
    for nombre, superadmin, activo in datos:
        user = _build_user(f"{nombre.lower()}-{marca}@example.com")
        user.full_name = f"{nombre} {marca}"
        user.is_superadmin = superadmin
        user.is_active = activo
        await repo.add(user)

    async def nombres(orden: CampoOrdenUsuarios, descendente: bool = False) -> list[str]:
        users, _ = await repo.list_page(
            page=1, size=10, query=marca, orden=orden, descendente=descendente
        )
        return [u.full_name.split()[0] for u in users]

    assert await nombres("usuario") == ["Ana", "Beto", "Ciro"]
    # "Administrador" antes que "Usuario"; empates por nombre.
    assert await nombres("rol") == ["Ana", "Beto", "Ciro"]
    assert await nombres("rol", descendente=True) == ["Beto", "Ciro", "Ana"]
    # "Activo" antes que "Inactivo".
    assert await nombres("estado") == ["Beto", "Ana", "Ciro"]
