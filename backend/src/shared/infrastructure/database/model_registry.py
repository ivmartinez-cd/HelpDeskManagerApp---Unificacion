"""Importa los modelos ORM de todos los módulos para que se registren en
Base.metadata antes de correr Alembic autogenerate o cualquier DDL. Un módulo
nuevo se suma acá cuando llegue (import con efecto secundario, sin uso directo).
"""

from src.modules.auth.infrastructure import models as _auth_models  # noqa: F401
