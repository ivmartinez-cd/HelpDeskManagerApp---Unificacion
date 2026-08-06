from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base compartida por los modelos ORM de todos los módulos."""
