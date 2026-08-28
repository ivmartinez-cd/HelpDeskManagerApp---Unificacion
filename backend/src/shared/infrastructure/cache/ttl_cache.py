"""Caché TTL genérica en memoria, para cómputos caros que se repiten en una ventana
corta (ej. varios tabs/reloads casi simultáneos pegando al mismo endpoint). No usar para
nada que deba ser consistente entre instancias del backend (single-process) ni para
datos que deban invalidarse activamente — no expone invalidate/clear, solo expira por
TTL. Ver la primera adopción en insumos (list_pending_orders.py)."""

import time
from collections.abc import Awaitable, Callable, Hashable
from dataclasses import dataclass


@dataclass
class _Entry[V]:
    value: V
    expires_at: float


class TTLCache[K: Hashable, V]:
    """Un solo loop de asyncio por proceso — sin lock: dos cómputos concurrentes para la
    misma key en una carrera pueden correr ambos (el segundo pisa al primero), nunca un
    resultado corrupto."""

    def __init__(self, ttl_seconds: float) -> None:
        self._ttl_seconds = ttl_seconds
        self._store: dict[K, _Entry[V]] = {}

    async def get_or_compute(self, key: K, compute: Callable[[], Awaitable[V]]) -> V:
        now = time.monotonic()
        entry = self._store.get(key)
        if entry is not None and entry.expires_at > now:
            return entry.value
        value = await compute()
        self._store[key] = _Entry(value=value, expires_at=now + self._ttl_seconds)
        return value
