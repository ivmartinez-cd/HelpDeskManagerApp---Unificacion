from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import Settings, get_settings


async def refresh_ers_token_with_playwright(
    token_file_path: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Usa Playwright en modo headless para iniciar sesión en Epson Remote Services (ERS),
    capturar el token Bearer y las cookies de Incapsula WAF, y guardarlos en `token_file_path`.

    Returns:
        Dict cargado desde el archivo JSON guardado.
    """
    cfg = settings or get_settings()
    username = cfg.epson_ers_username
    password = cfg.epson_ers_password.get_secret_value()

    out_path = Path(token_file_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()

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
            await page.goto(url, wait_until="networkidle")

            user_selector = (
                'input[type="text"], input[type="email"], '
                'input[placeholder="example@example.com"]'
            )
            await page.fill(user_selector, username)
            await page.fill('input[type="password"]', password)

            submit_selector = (
                'button.is-link, button:has-text("Iniciar sesión"), '
                'button:has-text("Log in")'
            )
            await page.click(submit_selector)

            for _ in range(30):
                if captured_token:
                    break
                await asyncio.sleep(0.5)

            if not captured_token:
                await browser.close()
                raise ExternalServiceError(
                    "No se pudo capturar el Bearer token de ERS durante el login con Playwright."
                )

            cookies = await context.cookies()
            await browser.close()

            token_data = {
                "token": captured_token,
                "cookies": cookies,
                "updated_at": datetime.now(UTC).isoformat(),
                "username": username,
            }

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(token_data, f, indent=2)

            return token_data

    except Exception as exc:
        if isinstance(exc, ExternalServiceError):
            raise
        raise ExternalServiceError(
            f"Fallo al renovar el token de ERS vía Playwright: {exc}"
        ) from exc
