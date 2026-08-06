from httpx import ASGITransport, AsyncClient

from src.shared.presentation.app import app


async def test_echo_with_invalid_body_returns_validation_envelope() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/health/echo", json={"message": ""})

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "detail" not in body
    assert isinstance(body["details"], list)


async def test_unknown_route_returns_envelope_not_default_detail() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert "detail" not in body
    assert body["code"] == "HTTP_ERROR"


async def test_request_id_header_is_always_present() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert "x-request-id" in response.headers
