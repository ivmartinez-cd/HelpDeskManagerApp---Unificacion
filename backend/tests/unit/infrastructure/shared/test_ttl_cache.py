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


async def test_pedidos_simultaneos_comparten_el_calculo_en_vuelo() -> None:
    cache: TTLCache[str, int] = TTLCache(ttl_seconds=60)
    calls = 0
    liberar = asyncio.Event()

    async def compute() -> int:
        nonlocal calls
        calls += 1
        await liberar.wait()
        return 7

    pedidos = [asyncio.create_task(cache.get_or_compute("k", compute)) for _ in range(3)]
    await asyncio.sleep(0)
    liberar.set()

    assert await asyncio.gather(*pedidos) == [7, 7, 7]
    assert calls == 1


async def test_un_error_no_se_cachea_y_llega_a_todos_los_que_esperaban() -> None:
    cache: TTLCache[str, int] = TTLCache(ttl_seconds=60)
    calls = 0

    async def falla() -> int:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0)
        raise RuntimeError("wsAyC caído")

    resultados = await asyncio.gather(
        cache.get_or_compute("k", falla), cache.get_or_compute("k", falla),
        return_exceptions=True,
    )
    assert all(isinstance(r, RuntimeError) for r in resultados)
    assert calls == 1
    assert await cache.get_or_compute("k", _const_int(5)) == 5  # el próximo reintenta


async def test_cancelar_al_que_lanzo_el_calculo_no_corta_a_los_demas() -> None:
    cache: TTLCache[str, int] = TTLCache(ttl_seconds=60)
    liberar = asyncio.Event()

    async def compute() -> int:
        await liberar.wait()
        return 9

    primero = asyncio.create_task(cache.get_or_compute("k", compute))
    segundo = asyncio.create_task(cache.get_or_compute("k", compute))
    await asyncio.sleep(0)
    primero.cancel()
    liberar.set()

    assert await segundo == 9


def _const_int(value: int) -> Callable[[], Awaitable[int]]:
    async def compute() -> int:
        return value

    return compute


def _const(value: str) -> Callable[[], Awaitable[str]]:
    async def compute() -> str:
        return value

    return compute
