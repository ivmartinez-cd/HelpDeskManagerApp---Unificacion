"""E2E manual del wizard APB (Asistente de KM) — driver a demanda, NO suite
(ADR-022): se corre a mano cuando se quiere re-verificar el flujo completo.

Requiere un usuario efímero (crearlo antes, borrarlo después):
    email  e2e.claude.temporal@canaldirecto.com.ar  ·  password abajo
    (superadmin en app_user; borrar también sus user_session al terminar)

Maneja el frontend REAL (next build servido) con Playwright desde el contenedor
del backend. Regla dura: NINGUNA request a los endpoints que gastan Google
(geocodificar-faltantes, calcular-distancias, auditar-pines) puede dispararse —
el script cancela todas las confirmaciones y falla si ve una.

Parte A (PENTACOM, sin base configurada): camino BLOQUEADO — el diagnóstico
muestra el bloqueante y el stepper de Distancias queda con candado.
Parte B (SAN JUAN, con base 2649): camino DESBLOQUEADO — entrar a Distancias
no dispara el preview, la confirmación de costo aparece y Cancelar no genera
requests; Ubicar corre el refresco gratis contra Siges; Pines lista cache-first.
"""

import re
import sys

from playwright.sync_api import sync_playwright

BASE = "http://frontend:3000"
EMAIL = "e2e.claude.temporal@canaldirecto.com.ar"
PASSWORD = "E2e-solo-local-2026!"
OUT = "/tmp/e2e"

BILLED = re.compile(r"geocodificar-faltantes|calcular-distancias|auditar-pines")

pasos_ok: list[str] = []
requests_api: list[str] = []
billed_hits: list[str] = []


def paso(nombre: str) -> None:
    pasos_ok.append(nombre)
    print(f"  OK  {nombre}")


def abrir_wizard(page, pst: str) -> None:  # noqa: ANN001
    page.goto(f"{BASE}/liquidaciones/configuracion/tabla-km")
    sel = page.locator('select[aria-label="Filtrar por PST"]')
    sel.wait_for(state="visible", timeout=20000)
    page.wait_for_function(
        "document.querySelector('select[aria-label=\"Filtrar por PST\"]').options.length > 1",
        timeout=20000,
    )
    labels = sel.locator("option").all_inner_texts()
    objetivo = next(o for o in labels if pst in o.upper())
    sel.select_option(label=objetivo)
    page.get_by_role("button", name=re.compile("Asistente de KM")).click()
    page.get_by_text("Esto es lo que el asistente encontró").wait_for(timeout=25000)


def stepper(page, nombre: str):  # noqa: ANN001
    return page.locator("button", has=page.locator(f"span:text-is('{nombre}')")).first


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        def on_request(r):  # noqa: ANN001
            if "/api/" in r.url:
                requests_api.append(f"{r.method} {r.url}")
                if BILLED.search(r.url):
                    billed_hits.append(f"{r.method} {r.url}")

        page.on("request", on_request)

        # Login
        page.goto(f"{BASE}/login")
        page.fill("#login-email", EMAIL)
        page.fill("#login-password", PASSWORD)
        page.click("button[type=submit]")
        page.wait_for_url(lambda u: "/login" not in u, timeout=20000)
        paso(f"login OK -> {page.url}")

        # ── Parte A: PENTACOM (sin base) — camino bloqueado ──
        abrir_wizard(page, "PENTACOM")
        page.screenshot(path=f"{OUT}/01-diagnostico-pentacom.png")
        assert [r for r in requests_api if "asistente-km/estado" in r], "sin GET estado"
        assert not billed_hits, f"el diagnóstico gastó Google: {billed_hits}"
        paso("A: diagnóstico PENTACOM cargó (0 endpoints pagos)")

        page.get_by_text("Falta la sucursal base de despacho").wait_for(timeout=5000)
        paso("A: bloqueante 'Falta la sucursal base' visible con instrucciones")

        assert stepper(page, "Distancias").is_disabled(), "Distancias debería estar bloqueado"
        paso("A: stepper Distancias bloqueado (candado) para PST sin base")

        # ── Parte B: SAN JUAN (base 2649) — camino desbloqueado ──
        # (abrir_wizard navega de nuevo, lo que cierra el modal anterior)
        abrir_wizard(page, "SAN JUAN")
        page.screenshot(path=f"{OUT}/02-diagnostico-sanjuan.png")
        paso("B: diagnóstico SAN JUAN cargó")

        boton_distancias = stepper(page, "Distancias")
        assert boton_distancias.is_enabled(), "Distancias debería estar habilitado (base 2649)"
        antes = len([r for r in requests_api if "calcular-distancias" in r])
        boton_distancias.click()
        page.wait_for_timeout(2500)
        despues = len([r for r in requests_api if "calcular-distancias" in r])
        assert despues == antes == 0, "REGRESIÓN: entrar a Distancias disparó el preview"
        page.screenshot(path=f"{OUT}/03-distancias-sin-autofetch.png")
        paso("B: entrar a Distancias NO disparó calcular-distancias (2.5s)")

        gate = page.get_by_role("button", name=re.compile("Calcular igual"))
        if gate.count() > 0:
            page.screenshot(path=f"{OUT}/04-gate-sin-ubicar.png")
            paso("B: gate 'sucursales sin ubicación' visible con las dos salidas explícitas")
            gate.click()  # decisión explícita: seguir igual (todavía NO consulta nada)
            page.wait_for_timeout(800)
        boton = page.get_by_role("button", name="Calcular distancias")
        if boton.count() > 0 and boton.first.is_enabled():
            boton.first.click()
            page.get_by_text("Esta acción consulta Google Maps").wait_for(timeout=8000)
            page.screenshot(path=f"{OUT}/05-confirmacion-google.png")
            page.get_by_role("button", name="Cancelar").click()
            page.wait_for_timeout(1200)
            assert not [r for r in requests_api if "calcular-distancias" in r], "Cancelar disparó el preview"
            paso("B: confirmación con estimación apareció; Cancelar => 0 requests")
        else:
            paso("B: botón Calcular no disponible (sin pendientes) — nada que confirmar")

        # Ubicar: refresco gratis real contra Siges
        stepper(page, "Ubicar").click()
        page.get_by_text("Actualizar datos desde Gestión").wait_for(timeout=10000)
        page.get_by_role("button", name="Actualizar desde Gestión").click()
        page.get_by_text(re.compile("sin cambios")).wait_for(timeout=45000)
        page.screenshot(path=f"{OUT}/06-ubicar-refrescado.png")
        assert not billed_hits, f"Ubicar gastó Google: {billed_hits}"
        paso("B: 'Actualizar desde Gestión' corrió contra Siges real (gratis) y mostró badges")

        # Pines: listado cache-first, sin disparar auditoría
        stepper(page, "Pines").click()
        page.get_by_text(re.compile("pin del mapa de Gestión")).wait_for(timeout=10000)
        page.wait_for_timeout(1500)
        page.screenshot(path=f"{OUT}/07-pines.png")
        assert not [r for r in requests_api if "auditar-pines" in r], "Pines auditó solo"
        paso("B: Pines cargó cache-first sin disparar la auditoría")

        print(f"\nRequests /api/ totales: {len(requests_api)}")
        print(f"Requests a endpoints PAGOS: {len(billed_hits)}")
        browser.close()
    return 1 if billed_hits else 0


if __name__ == "__main__":
    codigo = main()
    print(f"\n{'E2E PASS' if codigo == 0 else 'E2E FAIL'} — {len(pasos_ok)} pasos")
    sys.exit(codigo)
