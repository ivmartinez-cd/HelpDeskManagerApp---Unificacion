"""Factory del gateway de sla. Singleton de proceso (`lru_cache`) como los
gateways de insumos (ver wiring.py de ese módulo); acá no hay token que
cachear, pero tampoco hay razón para rearmar el connection string por request.

`lru_cache` no cachea excepciones: si MERCURIO no está configurado, cada
request reintenta la factory y devuelve el 502 con mensaje claro."""

from functools import lru_cache

from src.modules.sla.infrastructure.mercurio.pyodbc_sla_query_gateway import (
    PyodbcSlaQueryGateway,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import Settings, get_settings


def _connection_string(settings: Settings) -> str:
    encrypt = "yes" if settings.sla_mercurio_encrypt else "no"
    return (
        f"DRIVER={settings.sla_mercurio_driver};"
        f"SERVER={settings.sla_mercurio_host};"
        f"DATABASE={settings.sla_mercurio_database};"
        f"UID={settings.sla_mercurio_user};"
        f"PWD={settings.sla_mercurio_password.get_secret_value()};"
        f"Encrypt={encrypt};"
        "TrustServerCertificate=yes"
    )


@lru_cache
def get_sla_query_gateway() -> PyodbcSlaQueryGateway:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise ExternalServiceError(
            "La conexión a Siges (MERCURIO) no está configurada — falta SLA_MERCURIO_HOST"
        )
    return PyodbcSlaQueryGateway(
        _connection_string(settings), settings.sla_mercurio_timeout_seconds
    )
