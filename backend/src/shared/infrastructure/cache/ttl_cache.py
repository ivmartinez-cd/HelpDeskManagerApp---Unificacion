"""Caché TTL genérica en memoria, para cómputos caros que se repiten en una ventana
corta (ej. varios tabs/reloads casi simultáneos pegando al mismo endpoint). No usar para
nada que deba ser consistente entre instancias del backend (single-process) ni para
datos que deban invalidarse activamente — no expone invalidate/clear, solo expira por
TTL. Ver la primera adopción en insumos (list_pending_orders.py)."""

import asyncio
import time
from collections.abc import Awaitable, Callable, Hashable
from dataclasses import dataclass


@dataclass
class _Entry[V]:
    value: V
    expires_at: float


class TTLCache[K: Hashable, V]:
    """Un solo loop de asyncio por proceso. Deduplica cómputos en vuelo: si llega
    un segundo pedido para una key que se está calculando, espera ese mismo
    cálculo en vez de lanzar otro (el reporte de incidentes pide lo mismo desde
    dos endpoints a la vez y, sin esto, duplicaba las llamadas a wsAyC). Un error
    no se cachea: les llega a todos los que esperaban y el próximo pedido
    reintenta. El cálculo corre en su propia task, así que si el pedido que lo
    lanzó se cancela (cliente que cierra la pestaña) los demás igual lo reciben."""

    def __init__(self, ttl_seconds: float) -> None:
        self._ttl_seconds = ttl_seconds
        self._store: dict[K, _Entry[V]] = {}
        self._en_vuelo: dict[K, asyncio.Task[V]] = {}

    async def get_or_compute(self, key: K, compute: Callable[[], Awaitable[V]]) -> V:
        entry = self._store.get(key)
        if entry is not None and entry.expires_at > time.monotonic():
            return entry.value
        tarea = self._en_vuelo.get(key)
        if tarea is None:
            tarea = asyncio.ensure_future(self._calcular(key, compute))
            self._en_vuelo[key] = tarea
        return await asyncio.shield(tarea)

    async def _calcular(self, key: K, compute: Callable[[], Awaitable[V]]) -> V:
        try:
            value = await compute()
            self._store[key] = _Entry(value=value, expires_at=time.monotonic() + self._ttl_seconds)
            return value
        finally:
            del self._en_vuelo[key]
