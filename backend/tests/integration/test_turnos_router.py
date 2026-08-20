import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from src.shared.presentation.app import app


async def test_turnos_current_unauthenticated_returns_401() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/turnos/current")

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/turnos/casillas"),
        ("POST", "/api/turnos/casillas"),
        ("PUT", f"/api/turnos/casillas/{uuid.uuid4()}"),
        ("DELETE", f"/api/turnos/casillas/{uuid.uuid4()}"),
        ("GET", "/api/turnos/slots"),
        ("POST", "/api/turnos/slots"),
        ("PUT", f"/api/turnos/slots/{uuid.uuid4()}"),
        ("DELETE", f"/api/turnos/slots/{uuid.uuid4()}"),
        ("POST", f"/api/turnos/slots/{uuid.uuid4()}/asignaciones"),
        ("GET", "/api/turnos/users"),
        ("GET", "/api/turnos/grilla-variantes"),
        ("POST", "/api/turnos/grilla-variantes"),
        ("POST", "/api/turnos/grilla-variantes/precarga"),
        ("PUT", f"/api/turnos/grilla-variantes/{uuid.uuid4()}"),
        ("POST", f"/api/turnos/grilla-variantes/{uuid.uuid4()}/cancelar"),
    ],
)
async def test_turnos_admin_endpoints_unauthenticated_returns_401(
    method: str, path: str
) -> None:
    """Los endpoints de admin (listar/crear/editar/borrar casillas y slots,
    reasignar) exigen `admin:manage` -- sin sesión, 401 antes de llegar a chequear
    el permiso. No hay hoy infraestructura de test para armar una sesión
    autenticada sin el grant y confirmar el 403 (ningún otro test de integración
    del repo lo hace todavía); este test cubre el primer paso, fail-closed sin
    auth."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.request(method, path, json={})

    assert response.status_code == 401
