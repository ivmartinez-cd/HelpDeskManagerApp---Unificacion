import pytest

from src.modules.contadores.infrastructure.siges.pyodbc_operador_gateway import (
    PyodbcOperadorGateway,
)
from src.shared.domain.errors import ExternalServiceError


async def test_error_de_pyodbc_se_envuelve_en_external_service_error() -> None:
    """Un driver inexistente hace fallar el connect al instante (sin red); lo
    que importa es que al caller nunca le llegue la excepción cruda de pyodbc
    (ARCHITECTURE_GUIDE §6: infraestructura siempre envuelta)."""
    gateway = PyodbcOperadorGateway(
        "DRIVER={Driver Inexistente};SERVER=nohost;DATABASE=Siges;UID=x;PWD=x",
        timeout_seconds=1.0,
    )

    with pytest.raises(ExternalServiceError):
        await gateway.find_by_logins(["vipaez"])


async def test_lista_de_logins_vacia_no_conecta() -> None:
    gateway = PyodbcOperadorGateway(
        "DRIVER={Driver Inexistente};SERVER=nohost;DATABASE=Siges;UID=x;PWD=x",
        timeout_seconds=1.0,
    )

    assert await gateway.find_by_logins([]) == []
