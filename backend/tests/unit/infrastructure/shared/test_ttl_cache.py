"""Tests de TTLCache (caché genérica en memoria, primera adopción en
list_pending_orders.py)."""

import asyncio
from collections.abc import Awaitable, Callable

from src.shared.infrastructure.cache.ttl_cache import TTLCache


async def test_get_or_compute_cachea_dentro_del_ttl() -> None:
    cache: TTLCache[str, int] = TTLCache(ttl_seconds=60)
    calls = 0

    async def compute() -> int:
        nonlocal calls
        calls += 1
        return calls

    first = await cache.get_or_compute("k", compute)
    second = await cache.get_or_compute("k", compute)

    assert first == 1
    assert second == 1  # segundo hit dentro del TTL no vuelve a computar
    assert calls == 1


async def test_get_or_compute_expira_pasado_el_ttl() -> None:
    cache: TTLCache[str, int] = TTLCache(ttl_seconds=0.01)
    calls = 0

    async def compute() -> int:
        nonlocal calls
        calls += 1
        return calls

    await cache.get_or_compute("k", compute)
    await asyncio.sleep(0.02)
    second = await cache.get_or_compute("k", compute)

    assert second == 2
    assert calls == 2


async def test_keys_distintas_no_comparten_entrada() -> None:
    cache: TTLCache[tuple[int, bool], str] = TTLCache(ttl_seconds=60)

    a = await cache.get_or_compute((1, True), _const("a"))
    b = await cache.get_or_compute((1, False), _const("b"))

    assert a == "a"
    assert b == "b"


def _const(value: str) -> Callable[[], Awaitable[str]]:
    async def compute() -> str:
        return value

    return compute
