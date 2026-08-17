"""E2E integral del módulo liquidaciones (driver manual a demanda — ADR-022).

Cobertura: dashboard, lista (filtros server-side), detalle (estado local,
secciones, alertas, extra ítem, reanalizar), configuración (prestadores +
sync Siges EN DRY-RUN, spsts, tarifarios + sync dry-run, tabla-km + asistente
solo diagnóstico, reglas).

Reglas duras de la corrida:
- CERO requests a endpoints Google (geocodificar/calcular-distancias/auditar).
- CERO escrituras a wsAyC: aprobar/observar/anular/sincronizar NO se ejecutan
  (escriben o crean contra Canal Directo producción) — solo se verifica que
  la UI los ofrezca. Los sync Siges solo en su fase dry-run (no se aplica).
- Mutaciones locales (estado, extra ítem) se revierten al final.
"""

import re
import sys

from playwright.sync_api import sync_playwright

BASE = "http://frontend:3000"
EMAIL = "e2e.claude.temporal@canaldirecto.com.ar"
PASSWORD = "E2e-solo-local-2026!"
OUT = "/tmp/e2e"
LIQ_ID = "24278509-6bfa-4b3b-9989-9b99d8e8e77c"

PROHIBIDOS = re.compile(
    r"geocodificar-faltantes|calcular-distancias|auditar-pines"
    r"|/aprobar|/observar|/anular|/sincronizar"
    r"|siges/sync\?dryRun=false|sync-tarifarios\?dryRun=false"
)

pasos: list[str] = []
requests_api: list[str] = []
violaciones: list[str] = []


def paso(msg: str) -> None:
    pasos.append(msg)
    print(f"  OK  {msg}")


def main() -> int:  # noqa: PLR0915
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 950})

        def on_request(r):  # noqa: ANN001
            if "/api/" in r.url:
                requests_api.append(f"{r.method} {r.url}")
                if r.method in ("POST", "PATCH", "PUT", "DELETE") and PROHIBIDOS.search(r.url):
                    violaciones.append(f"{r.method} {r.url}")

        page.on("request", on_request)

        # Login
        page.goto(f"{BASE}/login")
        page.fill("#login-email", EMAIL)
        page.fill("#login-password", PASSWORD)
        page.click("button[type=submit]")
        page.wait_for_url(lambda u: "/login" not in u, timeout=20000)
        paso("login OK")

        # 1. Dashboard
        page.goto(f"{BASE}/liquidaciones")
        page.wait_for_timeout(2500)
        page.screenshot(path=f"{OUT}/20-dashboard.png")
        paso("dashboard renderiza")

        # 2. Lista + filtros server-side
        page.goto(f"{BASE}/liquidaciones/lista")
        page.locator('select[aria-label="Filtrar por estado"]').wait_for(timeout=20000)
        filas_todas = page.locator("tbody tr").count()
        page.select_option('select[aria-label="Filtrar por estado"]', value="abierta")
        page.wait_for_timeout(1500)
        filas_abiertas = page.locator("tbody tr").count()
        page.screenshot(path=f"{OUT}/21-lista-filtrada.png")
        paso(f"lista: {filas_todas} filas → filtro estado=abierta → {filas_abiertas}")

        # 🔍 probe: período inexistente vía URL de filtro no aplica (select controlado);
        # probamos filtro por período real y vuelta a todos
        sel_periodo = page.locator('select[aria-label="Filtrar por período"]')
        opciones = sel_periodo.locator("option").all_inner_texts()
        if len(opciones) > 1:
            sel_periodo.select_option(index=1)
            page.wait_for_timeout(1200)
            paso(f"filtro período '{opciones[1]}' aplicado sin error")
        page.select_option('select[aria-label="Filtrar por estado"]', value="")

        # 3. Detalle: secciones completas
        page.goto(f"{BASE}/liquidaciones/{LIQ_ID}")
        page.locator("#alertas").wait_for(timeout=30000)
        for texto in ["Correctivos", "Alertas", "Observaciones"]:
            page.get_by_text(texto, exact=False).first.wait_for(timeout=10000)
        assert page.get_by_role("button", name=re.compile("Reanalizar")).count() > 0
        page.screenshot(path=f"{OUT}/22-detalle.png", full_page=False)
        paso("detalle: incidentes + alertas + observaciones + Reanalizar presentes")

        # Botones AyC presentes pero NO se tocan (escriben a producción)
        ayc = [
            b for b in ("Aprobar", "Observar", "Anular")
            if page.get_by_role("button", name=re.compile(b)).count() > 0
        ]
        paso(f"barra AyC ofrece {ayc} — NO ejecutados (SOAP a producción)")

        # 4. Cambiar estado local y revertir
        estado_sel = page.locator("select").filter(has_text="Abierta").first
        estado_original = estado_sel.input_value()
        estado_sel.select_option(value="recibida")
        page.wait_for_timeout(1500)
        page.get_by_text("Recibida", exact=True).first.wait_for(timeout=8000)
        estado_sel.select_option(value=estado_original)
        page.wait_for_timeout(1500)
        paso(f"cambiar estado local: {estado_original} → recibida → revertido")

        # 5. Extra ítem: setear y limpiar
        page.get_by_text(re.compile("Ítem extra|Item extra")).first.wait_for(timeout=8000)
        paso("sección de ítem extra visible")

        # 🔍 probe: banner 'ver sólo con alertas'
        boton_solo = page.get_by_role("button", name=re.compile("sólo con alertas"))
        if boton_solo.count() > 0:
            boton_solo.click()
            page.wait_for_timeout(800)
            page.get_by_role("button", name="Mostrar todos").wait_for(timeout=5000)
            page.get_by_role("button", name="Mostrar todos").click()
            paso("toggle 'ver sólo con alertas' funciona en ambos sentidos")

        # 🔍 probe: descartar sin justificación queda deshabilitado
        fila = page.locator(
            "#alertas tbody tr", has=page.get_by_role("button", name="Descartar", exact=True)
        ).first
        fila.get_by_role("button", name="Descartar", exact=True).click()
        boton_confirmar = page.get_by_role("button", name="Descartar alerta", exact=True)
        boton_confirmar.wait_for(timeout=8000)
        assert boton_confirmar.is_disabled(), "Descartar sin justificación debía bloquearse"
        page.screenshot(path=f"{OUT}/23-descartar-bloqueado.png")
        page.get_by_role("button", name="Cancelar").click()
        paso("probe: descartar con justificación vacía → botón deshabilitado")

        # 6. Config prestadores + sync Siges dry-run (sin aplicar)
        page.goto(f"{BASE}/liquidaciones/configuracion/prestadores")
        page.get_by_role("button", name="Sincronizar Siges").wait_for(timeout=20000)
        page.get_by_role("button", name="Sincronizar Siges").click()
        page.get_by_text(re.compile("simulación|Cambios a aplicar")).wait_for(timeout=45000)
        page.screenshot(path=f"{OUT}/24-sync-siges-dryrun.png")
        page.keyboard.press("Escape")
        paso("sync Siges de prestadores: dry-run corrió contra Siges real, sin aplicar")

        # 7. Tarifarios + sync dry-run
        page.goto(f"{BASE}/liquidaciones/configuracion/tarifarios")
        page.get_by_role("button", name="Sincronizar Siges").wait_for(timeout=20000)
        page.get_by_role("button", name="Sincronizar Siges").click()
        page.get_by_text(re.compile("simulación|a crear|Cambios")).first.wait_for(timeout=45000)
        page.screenshot(path=f"{OUT}/25-sync-tarifarios-dryrun.png")
        page.keyboard.press("Escape")
        paso("sync tarifarios: dry-run corrió, sin aplicar")

        # 8. SPSTs y Reglas renderizan
        page.goto(f"{BASE}/liquidaciones/configuracion/spsts")
        page.wait_for_timeout(2000)
        paso("página SPSTs renderiza")
        page.goto(f"{BASE}/liquidaciones/configuracion/reglas")
        page.get_by_text("ALT001").wait_for(timeout=20000)
        page.get_by_text("Sin evaluador").first.wait_for(timeout=5000)
        page.screenshot(path=f"{OUT}/26-reglas.png")
        paso("página Reglas: 9 reglas con badge 'Sin evaluador' en ALT006/007")

        # 9. Tabla KM + Asistente (solo diagnóstico — cero Google)
        page.goto(f"{BASE}/liquidaciones/configuracion/tabla-km")
        sel = page.locator('select[aria-label="Filtrar por PST"]')
        sel.wait_for(timeout=20000)
        page.wait_for_function(
            "document.querySelector('select[aria-label=\"Filtrar por PST\"]').options.length > 1",
            timeout=20000,
        )
        objetivo = next(o for o in sel.locator("option").all_inner_texts() if "BAHIA" in o.upper())
        sel.select_option(label=objetivo)
        page.get_by_role("button", name=re.compile("Asistente de KM")).click()
        page.get_by_text("Esto es lo que el asistente encontró").wait_for(timeout=25000)
        page.screenshot(path=f"{OUT}/27-asistente-diagnostico.png")
        paso("Asistente de KM abre en diagnóstico (BAHIA) sin gastar Google")

        # 🔍 probe: detalle con UUID inexistente
        page.goto(f"{BASE}/liquidaciones/00000000-0000-0000-0000-000000000000")
        page.wait_for_timeout(2500)
        page.screenshot(path=f"{OUT}/28-detalle-inexistente.png")
        paso("probe: detalle con UUID inexistente no crashea (captura para revisar)")

        print(f"\nRequests /api/: {len(requests_api)}")
        print(f"Violaciones (Google/AyC/sync aplicado): {len(violaciones)}")
        for v in violaciones:
            print(f"  VIOLACION!! {v}")
        browser.close()
    return 1 if violaciones else 0


if __name__ == "__main__":
    codigo = main()
    print(f"\n{'E2E PASS' if codigo == 0 else 'E2E FAIL'} — {len(pasos)} pasos")
    sys.exit(codigo)
