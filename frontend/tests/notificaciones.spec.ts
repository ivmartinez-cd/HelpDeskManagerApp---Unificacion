import type { Page, Route } from "@playwright/test";
import { test, expect } from "./fixtures";

// Campanita del header (bandeja de notificaciones): badge con las no leídas,
// panel con historial, "marcar todas", y toast para las que llegan con la
// pestaña abierta. Todo mockeado con page.route: no toca el backend real.

interface Notif {
  id: string;
  titulo: string;
  cuerpo: string;
  url: string | null;
  creada_en: string;
  leida: boolean;
}

const vieja: Notif = {
  id: "11111111-1111-1111-1111-111111111111",
  titulo: "Caso 844833: hay una visita en la misma sucursal",
  cuerpo: "Granja Tres Arroyos — Planta Pinazo. Caso 838123 derivado.",
  url: "/sla/mesa-de-ayuda",
  creada_en: "2026-09-30T14:00:00Z",
  leida: false,
};

const nueva: Notif = {
  ...vieja,
  id: "22222222-2222-2222-2222-222222222222",
  titulo: "Caso 900001: hay una visita en la misma sucursal",
};

function respuesta(items: Notif[]) {
  return JSON.stringify({ items, total: items.length, page: 1, size: 20 });
}

async function mockBandeja(page: Page, estado: { noLeidas: Notif[]; marcadas: unknown[] }) {
  await page.route("**/api/notificaciones/marcar-leidas", async (route: Route) => {
    estado.marcadas.push(route.request().postDataJSON());
    estado.noLeidas = [];
    await route.fulfill({ contentType: "application/json", body: '{"actualizadas":1}' });
  });
  // Mismas filas para "no leídas" (polling) y para el historial del panel.
  await page.route("**/api/notificaciones?*", (route: Route) =>
    route.fulfill({ contentType: "application/json", body: respuesta(estado.noLeidas) }),
  );
}

test.describe("Notificaciones", () => {
  test("badge, panel y marcar todas como leídas", async ({ page }) => {
    const estado = { noLeidas: [vieja], marcadas: [] as unknown[] };
    await mockBandeja(page, estado);

    await page.goto("/");
    const campanita = page.getByRole("button", { name: "Notificaciones: 1 sin leer" });
    await expect(campanita).toBeVisible();

    await campanita.click();
    await expect(page.getByText(vieja.titulo)).toBeVisible();

    await page.getByRole("button", { name: "Marcar todas como leídas" }).click();
    expect(estado.marcadas).toEqual([{ ids: null }]);
    await expect(page.getByRole("button", { name: "Notificaciones", exact: true })).toBeVisible();
  });

  test("una notificación que llega con la pestaña abierta muestra un toast", async ({ page }) => {
    await page.clock.install();
    const estado = { noLeidas: [vieja], marcadas: [] as unknown[] };
    await mockBandeja(page, estado);

    await page.goto("/");
    await expect(page.getByRole("button", { name: "Notificaciones: 1 sin leer" })).toBeVisible();
    // La que ya estaba al cargar no se anuncia: solo el badge.
    await expect(page.getByText(vieja.titulo)).toHaveCount(0);

    estado.noLeidas = [nueva, vieja];
    await page.clock.fastForward(31_000);

    await expect(page.getByRole("button", { name: "Notificaciones: 2 sin leer" })).toBeVisible();
    await expect(page.getByText(nueva.titulo)).toBeVisible();
    await expect(page.getByText(vieja.titulo)).toHaveCount(0);
  });
});
