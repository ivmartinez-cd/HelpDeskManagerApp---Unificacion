"""E2E manual de la gestión de alertas ALT (driver a demanda, no suite — ADR-022).

Flujo verificado contra la app real:
1. Descartar una alerta (no-ALT001) con justificación → Reanalizar → sigue
   descartada con su motivo (conciliar_alertas en vivo).
2. Desactivar ALT001 en Configuración → Reglas → Reanalizar → las ALT001
   desaparecen → reactivar → Reanalizar → vuelven pendientes.

Requiere el usuario efímero (crear antes / borrar después)."""

import re
import sys

from playwright.sync_api import sync_playwright

BASE = "http://frontend:3000"
EMAIL = "e2e.claude.temporal@canaldirecto.com.ar"
PASSWORD = "E2e-solo-local-2026!"
OUT = "/tmp/e2e"
LIQ_ID = "24278509-6bfa-4b3b-9989-9b99d8e8e77c"
MOTIVO = "Prueba E2E: diferencia acordada con el prestador"

pasos: list[str] = []


def paso(msg: str) -> None:
    pasos.append(msg)
    print(f"  OK  {msg}")


def reanalizar(page) -> None:  # noqa: ANN001
    page.get_by_role("button", name=re.compile("Reanalizar")).click()
    page.wait_for_timeout(1000)
    page.get_by_role("button", name=re.compile("Reanalizar")).wait_for(timeout=60000)
    page.wait_for_timeout(1500)  # re-load del detalle


def filas_alertas(page):  # noqa: ANN001
    return page.locator("#alertas tbody tr")


def toggle_alt001(page, activar: bool) -> None:  # noqa: ANN001
    page.goto(f"{BASE}/liquidaciones/configuracion/reglas")
    page.get_by_text("Reglas de alerta").first.wait_for(timeout=20000)
    fila = page.locator("tr", has=page.locator("td", has_text="ALT001")).first
    switch = fila.get_by_role("switch")
    estado = switch.get_attribute("aria-checked")
    if (estado == "true") != activar:
        switch.click()
        page.wait_for_timeout(1200)
    assert switch.get_attribute("aria-checked") == ("true" if activar else "false")


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 950})

        page.goto(f"{BASE}/login")
        page.fill("#login-email", EMAIL)
        page.fill("#login-password", PASSWORD)
        page.click("button[type=submit]")
        page.wait_for_url(lambda u: "/login" not in u, timeout=20000)
        paso("login OK")

        # 1. Sección Alertas visible con filtros
        page.goto(f"{BASE}/liquidaciones/{LIQ_ID}")
        page.locator("#alertas").wait_for(timeout=30000)
        total_inicial = filas_alertas(page).count()
        assert total_inicial > 0, "sin filas de alertas"
        page.locator("#alertas").scroll_into_view_if_needed()
        page.screenshot(path=f"{OUT}/10-seccion-alertas.png")
        paso(f"sección Alertas visible con {total_inicial} filas y acciones")

        # 2. Descartar una alerta NO-ALT001 (pendiente: tiene botón Descartar)
        objetivo = page.locator(
            "#alertas tbody tr",
            has=page.get_by_role("button", name="Descartar", exact=True),
            has_not=page.locator("td", has_text="ALT001"),
        ).first
        tipo = objetivo.locator("td").first.inner_text().strip()
        objetivo.get_by_role("button", name="Descartar", exact=True).click()
        page.get_by_text(re.compile("NO va a volver a aparecer")).wait_for(timeout=8000)
        page.locator("textarea").fill(MOTIVO)
        page.screenshot(path=f"{OUT}/11-descartar-modal.png")
        page.get_by_role("button", name="Descartar alerta", exact=True).click()
        page.get_by_text(f"Motivo: {MOTIVO}").wait_for(timeout=15000)
        paso(f"alerta {tipo} descartada con justificación")

        # 3. EL test: reanalizar y verificar que sigue descartada con su motivo
        reanalizar(page)
        page.locator("#alertas").scroll_into_view_if_needed()
        page.get_by_text(f"Motivo: {MOTIVO}").wait_for(timeout=15000)
        page.screenshot(path=f"{OUT}/12-descartada-sobrevive-reanalisis.png")
        paso("re-análisis conservó la alerta descartada CON su motivo")

        # 4. Desactivar ALT001 → reanalizar → desaparecen
        alt001_antes = page.locator("#alertas tbody td", has_text="ALT001").count()
        assert alt001_antes > 0, "no había ALT001 para el test de regla"
        toggle_alt001(page, activar=False)
        page.screenshot(path=f"{OUT}/13-regla-alt001-off.png")
        paso("regla ALT001 desactivada en Configuración → Reglas")

        page.goto(f"{BASE}/liquidaciones/{LIQ_ID}")
        page.locator("#alertas").wait_for(timeout=30000)
        reanalizar(page)
        page.locator("#alertas").wait_for(timeout=30000)
        alt001_despues = page.locator("#alertas tbody td", has_text="ALT001").count()
        assert alt001_despues == 0, f"quedaron {alt001_despues} ALT001 con la regla apagada"
        page.get_by_text(f"Motivo: {MOTIVO}").wait_for(timeout=10000)  # la descartada sigue
        page.screenshot(path=f"{OUT}/14-sin-alt001.png")
        paso(
            f"con ALT001 apagada: {alt001_antes} → 0 ALT001 (la descartada no-ALT001 sigue)"
        )

        # 5. Reactivar → reanalizar → vuelven pendientes
        toggle_alt001(page, activar=True)
        page.goto(f"{BASE}/liquidaciones/{LIQ_ID}")
        page.locator("#alertas").wait_for(timeout=30000)
        reanalizar(page)
        page.locator("#alertas").wait_for(timeout=30000)
        alt001_final = page.locator("#alertas tbody td", has_text="ALT001").count()
        assert alt001_final > 0, "las ALT001 no volvieron al reactivar la regla"
        paso(f"regla reactivada: {alt001_final} ALT001 de vuelta (pendientes)")

        browser.close()
    return 0


if __name__ == "__main__":
    codigo = main()
    print(f"\n{'E2E PASS' if codigo == 0 else 'E2E FAIL'} — {len(pasos)} pasos")
    sys.exit(codigo)
