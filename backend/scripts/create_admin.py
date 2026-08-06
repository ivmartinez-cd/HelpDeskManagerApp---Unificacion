"""Crea el primer usuario superadmin. Uso: `uv run python scripts/create_admin.py`.

Script operativo, fuera de las capas domain/application/infrastructure: es una
utilidad de arranque de un solo uso, no parte del flujo de negocio de la app.
El password se pide de forma interactiva (getpass) — nunca por argv, para que
no quede en el historial de la shell ni en logs de proceso.
"""

import asyncio
import getpass

from argon2 import PasswordHasher

from src.modules.auth.infrastructure.models import AppUser
from src.shared.infrastructure.database.session import get_sessionmaker


async def _create_admin(email: str, full_name: str, password: str) -> None:
    hasher = PasswordHasher()
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        user = AppUser(
            email=email.strip().lower(),
            full_name=full_name.strip(),
            password_hash=hasher.hash(password),
            is_superadmin=True,
        )
        session.add(user)
        await session.commit()
        print(f"Superadmin creado: {user.email} ({user.id})")


def _read_credentials() -> tuple[str, str, str]:
    email = input("Email: ").strip()
    full_name = input("Nombre completo: ").strip()
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirmar password: ")
    if password != confirm:
        raise SystemExit("Las contraseñas no coinciden.")
    return email, full_name, password


def main() -> None:
    email, full_name, password = _read_credentials()
    asyncio.run(_create_admin(email, full_name, password))


if __name__ == "__main__":
    main()
