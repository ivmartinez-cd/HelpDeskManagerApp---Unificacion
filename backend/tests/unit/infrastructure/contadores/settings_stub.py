"""Settings de test para los adapters httpx de contadores — construida
explícitamente (sin leer el .env real) para que los tests no dependan del
entorno ni toquen credenciales verdaderas."""

from typing import Any

from src.shared.infrastructure.config.settings import Settings


def make_settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "frontend_url": "http://front.test",
        "cors_origin": "http://front.test",
        "database_url": "postgresql+asyncpg://x:x@localhost/x",
        "epson_ers_username": "ers@test.local",
        "epson_ers_password": "pw-test",
        "epson_ers_base_url": "https://ers.test/prod",
        "gestion_web_username": "gestion-user",
        "gestion_web_password": "pw-test",
        "gestion_web_base_url": "http://gestion.test",
        "sds_base_url": "https://sds.test/PortalAPI",
        "sds_api_key": "key",
        "sds_api_secret": "secret",
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)
