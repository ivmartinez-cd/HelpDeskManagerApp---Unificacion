from __future__ import annotations

import asyncio
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import Settings, get_settings


def _sync_refresh_ers_token(token_file_path: str, cfg: Settings) -> dict[str, Any]:
    username = cfg.epson_ers_username
    password = cfg.epson_ers_password.get_secret_value()

    out_path = Path(token_file_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        captured_token: str | None = None

        def handle_request(request: object) -> None:
            nonlocal captured_token
            headers = getattr(request, "headers", {})
            auth = headers.get("authorization")
            if (
                auth
                and auth.startswith("Bearer ")
                and (not captured_token or len(auth) > len(captured_token))
            ):
                captured_token = auth

        page.on("request", handle_request)

        url = "https://www.remote-services.epson.com/"
        page.goto(url, wait_until="networkidle")

        user_selector = (
            'input[type="text"], input[type="email"], '
            'input[placeholder="example@example.com"]'
        )
        page.fill(user_selector, username)
        page.fill('input[type="password"]', password)

        submit_selector = (
            'button.is-link, button:has-text("Iniciar sesión"), '
            'button:has-text("Log in")'
        )
        page.click(submit_selector)

        # El login pasa por el desafío anti-bot de Incapsula antes de dejar pasar la
        # request autenticada: en un datacenter (Docker) puede demorar ~45s, muy por
        # encima de los <10s típicos desde una IP residencial/de oficina.
        for _ in range(180):
            if captured_token:
                break
            time.sleep(0.5)

        if not captured_token:
            browser.close()
            raise ExternalServiceError(
                "No se pudo capturar el Bearer token de ERS durante el login con Playwright."
            )

        cookies = context.cookies()
        browser.close()

        token_data = {
            "token": captured_token,
            "cookies": cookies,
            "updated_at": datetime.now(UTC).isoformat(),
            "username": username,
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2)

        return token_data


async def refresh_ers_token_with_playwright(
    token_file_path: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Usa Playwright en modo headless para iniciar sesión en Epson Remote Services (ERS),
    capturar el token Bearer y las cookies de Incapsula WAF, y guardarlos en `token_file_path`.

    Ejecuta el navegador en un hilo de trabajo dedicado (`asyncio.to_thread`) para garantizar
    compatibilidad completa en Windows sin conflictos de EventLoop.

    Returns:
        Dict cargado desde el archivo JSON guardado.
    """
    cfg = settings or get_settings()
    try:
        return await asyncio.to_thread(_sync_refresh_ers_token, token_file_path, cfg)
    except Exception as exc:
        if isinstance(exc, ExternalServiceError):
            raise
        raise ExternalServiceError(
            f"Fallo al renovar el token de ERS vía Playwright: {exc}"
        ) from exc
