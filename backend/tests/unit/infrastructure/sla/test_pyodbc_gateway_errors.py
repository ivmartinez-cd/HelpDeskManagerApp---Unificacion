import pytest

from src.modules.sla.domain.value_objects.periodo import Periodo
from src.modules.sla.infrastructure.mercurio.pyodbc_sla_query_gateway import (
    PyodbcSlaQueryGateway,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


async def test_error_de_pyodbc_se_envuelve_en_external_service_error() -> None:
    """Un driver inexistente hace fallar el connect al instante (sin red); lo
    que importa es que al caller nunca le llegue la excepción cruda de pyodbc
    (ARCHITECTURE_GUIDE §6: infraestructura siempre envuelta — hoy en el
    MercurioQueryRunner compartido, ADR-018)."""
    gateway = PyodbcSlaQueryGateway(
        MercurioQueryRunner(
            "DRIVER={Driver Inexistente};SERVER=nohost;DATABASE=Siges;UID=x;PWD=x",
            timeout_seconds=1.0,
        )
    )

    with pytest.raises(ExternalServiceError):
        await gateway.find_incidentes(Periodo(202608))
