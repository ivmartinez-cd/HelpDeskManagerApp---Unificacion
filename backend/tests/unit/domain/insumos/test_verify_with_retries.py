from src.modules.insumos.domain.services.verify_with_retries import verify_with_retries


async def test_confirms_on_first_try() -> None:
    calls = 0

    async def check() -> bool:
        nonlocal calls
        calls += 1
        return True

    assert await verify_with_retries(check, delays=(0, 0, 0)) is True
    assert calls == 1


async def test_replicates_real_incident_confirms_on_third_attempt() -> None:
    """Pedido real 443017/SDS-974325 (2026-08-03, ver
    SDSINSUMOS_CARACTERIZACION_BACKEND.md §3.2): la primera verificación no
    vio el pedido recién creado por lag de lectura de Canal Directo, recién
    se confirmó unos segundos después."""
    attempts = [False, False, True]

    async def check() -> bool:
        return attempts.pop(0)

    assert await verify_with_retries(check, delays=(0, 0, 0, 0)) is True


async def test_returns_false_when_it_never_confirms() -> None:
    async def check() -> bool:
        return False

    assert await verify_with_retries(check, delays=(0, 0, 0)) is False
