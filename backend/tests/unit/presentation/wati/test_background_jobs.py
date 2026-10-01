"""Job wati_sync: un ciclo comitea lo sincronizado y un error no corta el loop.
Todo con fakes: nunca llama a la API real de WATI."""

import asyncio
import logging
from types import SimpleNamespace
from typing import Any

import pytest

from src.modules.wati.presentation import background_jobs


class _Sesion:
    def __init__(self) -> None:
        self.commits = 0

    async def __aenter__(self) -> "_Sesion":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1


async def test_ciclo_sincroniza_y_comitea(monkeypatch: pytest.MonkeyPatch) -> None:
    sesion = _Sesion()
    resultado = SimpleNamespace(contactos_revisados=3, esperando=1, descartados=2)

    class _Sync:
        async def execute(self) -> Any:
            return resultado

    monkeypatch.setattr(background_jobs, "get_sessionmaker", lambda: lambda: sesion)
    monkeypatch.setattr(background_jobs, "build_sync_conversaciones", lambda _s: _Sync())

    await background_jobs._ciclo_sync()

    assert sesion.commits == 1


async def test_un_ciclo_fallido_se_loguea_y_el_loop_sigue(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    intentos: list[int] = []
    esperas: list[float] = []

    async def _falla() -> None:
        intentos.append(1)
        raise RuntimeError("WATI caído")

    async def _dormir(segundos: float) -> None:
        esperas.append(segundos)
        if len(esperas) == 2:
            raise asyncio.CancelledError

    monkeypatch.setattr(background_jobs, "_ciclo_sync", _falla)
    monkeypatch.setattr(background_jobs.asyncio, "sleep", _dormir)

    with caplog.at_level(logging.ERROR), pytest.raises(asyncio.CancelledError):
        await background_jobs.background_wati_sync_task(interval_minutes=5)

    assert len(intentos) == 2
    assert esperas == [300, 300]
    assert "wati_sync: ciclo fallido" in caplog.text
