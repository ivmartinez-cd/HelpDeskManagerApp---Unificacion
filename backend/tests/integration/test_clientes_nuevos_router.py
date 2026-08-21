import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from src.shared.presentation.app import app


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/contadores/clientes-nuevos"),
        ("GET", "/api/contadores/clientes-nuevos/candidatos"),
        ("POST", "/api/contadores/clientes-nuevos"),
        ("PUT", f"/api/contadores/clientes-nuevos/{uuid.uuid4()}"),
        ("DELETE", f"/api/contadores/clientes-nuevos/{uuid.uuid4()}"),
    ],
)
async def test_clientes_nuevos_endpoints_unauthenticated_returns_401(
    method: str, path: str
) -> None:
    """Todas las fichas de clientes nuevos exigen `contadores.manage`; sin
    sesión, 401 antes de llegar al permiso (mismo criterio que
    test_turnos_router.py: fail-closed sin auth)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.request(method, path, json={})

    assert response.status_code == 401
