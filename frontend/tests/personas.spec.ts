import type { Page, Route } from "@playwright/test";
import type { Persona } from "../src/features/personas/api/personas-api";
import { expect, test } from "./fixtures";

// ── Datos mock (wire camelCase, serialization_alias de persona_schemas.py) ──

const SECTOR_ID = "aaaaaaaa-0000-0000-0000-000000000001";
const CARGO_ID = "bbbbbbbb-0000-0000-0000-000000000001";
const LAURA_ID = "cccccccc-0000-0000-0000-000000000001";
const PEDRO_ID = "cccccccc-0000-0000-0000-000000000002";
const LAURA_USER_ID = "dddddddd-0000-0000-0000-000000000001";

const LAURA: Persona = {
  id: LAURA_ID,
  firstName: "Laura",
  lastName: "Pérez",
  email: "lperez@canal.com",
  color: "#2563eb",
  activa: true,
  sectorId: SECTOR_ID,
  sectorNombre: "Soporte Técnico",
  cargoNombre: "Analista Senior",
  entraALaApp: true,
  acceso: { userId: LAURA_USER_ID, activo: true, superadmin: false, ultimoIngreso: null },
};

const PEDRO: Persona = {
  ...LAURA,
  id: PEDRO_ID,
  firstName: "Pedro",
  lastName: "Acosta",
  email: "pacosta@canal.com",
  color: "#059669",
  entraALaApp: false,
  acceso: null,
};

const SALDO = { annual: 21, carryOver: 0, used: 7, pending: 0, available: 14, cycleOpen: true };

function empleado(p: Persona, userId: string | null) {
  return {
    id: p.id,
    firstName: p.firstName,
    lastName: p.lastName,
    email: p.email,
    hireDate: "2019-03-15",
    status: "ACTIVE",
    color: p.color,
    departmentId: SECTOR_ID,
    cargoId: CARGO_ID,
    userId,
    sigesEmpresaId: null,
    sectorNombre: p.sectorNombre,
    sectorColor: "#2563eb",
    cargoNombre: p.cargoNombre,
    diasAnuales: 21,
    antiguedadAnios: 7.5,
    saldo: SALDO,
    saldoSiguiente: null,
  };
}

const SECTOR = { id: SECTOR_ID, name: "Soporte Técnico", color: "#2563eb", empleadosCount: 2, jefes: [] };
const CARGO = { id: CARGO_ID, name: "Analista Senior", maxSimultaneos: null, empleadosCount: 2 };

function page_(items: unknown[]) {
  return JSON.stringify({ items, total: items.length, page: 1, size: 200 });
}

function json(route: Route, body: unknown) {
  return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
}

interface Llamadas {
  patchDatos: unknown[];
  putEmpleado: unknown[];
  acceso: string[];
  borrados: string[];
}

/** Mock de /api/personas y de los catálogos de Gestión de Personal. Devuelve
 * lo que la pantalla mandó al backend, para verificarlo. */
async function mockPersonas(page: Page): Promise<Llamadas> {
  const llamadas: Llamadas = { patchDatos: [], putEmpleado: [], acceso: [], borrados: [] };
  const personas = new Map([
    [LAURA_ID, { ...LAURA }],
    [PEDRO_ID, { ...PEDRO }],
  ]);
  await page.route("**/api/personas**", async (route) => {
    const req = route.request();
    const path = new URL(req.url()).pathname;
    if (path === "/api/personas") return route.fulfill({ status: 200, contentType: "application/json", body: page_([...personas.values()]) });
    const [, , , id, accion] = path.split("/");
    const actual = personas.get(id)!;
    if (accion === "datos") {
      llamadas.patchDatos.push(req.postDataJSON());
      Object.assign(actual, req.postDataJSON());
    } else if (accion === "acceso") {
      llamadas.acceso.push(req.method());
      const activo = req.method() === "POST";
      actual.acceso = { userId: LAURA_USER_ID, activo, superadmin: false, ultimoIngreso: null };
      actual.entraALaApp = activo;
    }
    return json(route, actual);
  });
  await page.route("**/api/vacaciones/empleados**", (route) => {
    if (route.request().method() === "PUT") {
      llamadas.putEmpleado.push(route.request().postDataJSON());
      return json(route, { id: LAURA_ID });
    }
    if (route.request().method() === "DELETE") {
      llamadas.borrados.push(new URL(route.request().url()).pathname.split("/").pop()!);
      return route.fulfill({ status: 204 });
    }
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: page_([empleado(LAURA, LAURA_USER_ID), empleado(PEDRO, null)]),
    });
  });
  await page.route("**/api/vacaciones/sectores**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: page_([SECTOR]) }),
  );
  await page.route("**/api/vacaciones/cargos**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: page_([CARGO]) }),
  );
  return llamadas;
}

test.describe("Personas", () => {
  test("listado: datos laborales, filtro por acceso y orden por nombre", async ({ page }) => {
    await mockPersonas(page);
    await page.goto("/personas");

    await expect(page.getByRole("heading", { name: "Personas" })).toBeVisible();
    await expect(page.getByText("Laura Pérez")).toBeVisible();
    await expect(page.getByText("Pedro Acosta")).toBeVisible();
    await expect(page.getByRole("columnheader", { name: /Disponibles/ })).toBeVisible();
    await expect(page.getByText("15/03/2019").first()).toBeVisible();

    // Orden: nombre ascendente por default (Laura antes que Pedro); al invertir, al revés.
    const nombres = page.locator("tbody tr td:first-child a span span:first-child");
    await expect(nombres).toHaveText(["Laura Pérez", "Pedro Acosta"]);
    await page.getByRole("columnheader", { name: /Nombre/ }).getByRole("button").click();
    await expect(nombres).toHaveText(["Pedro Acosta", "Laura Pérez"]);

    await page.getByLabel("Entra a la app").selectOption("no");
    await expect(page.getByText("Pedro Acosta")).toBeVisible();
    await expect(page.getByText("Laura Pérez")).toHaveCount(0);
  });

  test("ficha: editar datos manda nombre, mail y color juntos", async ({ page }) => {
    const llamadas = await mockPersonas(page);
    await page.goto("/personas");
    await page.getByText("Laura Pérez").click();

    await expect(page).toHaveURL(new RegExp(`/personas/${LAURA_ID}$`));
    await expect(page.getByRole("heading", { name: "Laura Pérez" })).toBeVisible();
    const guardar = page.getByRole("button", { name: "Guardar cambios" });
    await expect(guardar).toBeDisabled();

    await page.getByLabel("Nombre").fill("Laura Inés");
    await page.getByLabel("Color de identidad").fill("#ff00aa");
    await guardar.click();

    await expect(page.getByText("Datos guardados")).toBeVisible();
    expect(llamadas.patchDatos).toEqual([
      { firstName: "Laura Inés", lastName: "Pérez", email: "lperez@canal.com", color: "#ff00aa" },
    ]);
    await expect(page.getByRole("heading", { name: "Laura Inés Pérez" })).toBeVisible();
  });

  test("ficha laboral: guardar conserva la cuenta vinculada", async ({ page }) => {
    const llamadas = await mockPersonas(page);
    await page.goto(`/personas/${LAURA_ID}`);
    await page.getByRole("button", { name: "Laboral" }).click();

    await expect(page.getByText("Disponibles")).toBeVisible();
    await page.getByLabel("Estado").selectOption("INACTIVE");
    await page.getByRole("button", { name: "Guardar cambios" }).click();

    await expect(page.getByText("Datos laborales guardados")).toBeVisible();
    expect(llamadas.putEmpleado).toEqual([
      expect.objectContaining({ status: "INACTIVE", userId: LAURA_USER_ID, email: "lperez@canal.com" }),
    ]);
  });

  test("eliminar: solo sin acceso a la app, confirma y vuelve al listado", async ({ page }) => {
    const llamadas = await mockPersonas(page);
    await page.goto(`/personas/${LAURA_ID}`);
    await page.getByRole("button", { name: "Laboral" }).click();
    await expect(page.getByRole("button", { name: "Eliminar persona" })).toBeDisabled();

    await page.goto(`/personas/${PEDRO_ID}`);
    await page.getByRole("button", { name: "Laboral" }).click();
    page.once("dialog", (d) => void d.accept());
    await page.getByRole("button", { name: "Eliminar persona" }).click();

    await expect(page).toHaveURL(/\/personas$/);
    expect(llamadas.borrados).toEqual([PEDRO_ID]);
  });

  test("acceso: quitar y volver a dar acceso a la app", async ({ page }) => {
    const llamadas = await mockPersonas(page);
    await page.goto(`/personas/${LAURA_ID}`);
    await page.getByRole("button", { name: "Acceso a la app" }).click();

    await expect(page.getByRole("link", { name: "Permisos" })).toHaveAttribute(
      "href",
      `/admin/usuarios/${LAURA_USER_ID}/permisos`,
    );
    page.once("dialog", (d) => void d.accept());
    await page.getByRole("button", { name: "Quitar acceso" }).click();
    // El badge de estado pasa a "Acceso quitado" y el botón a "Reactivar".
    const reactivar = page.getByRole("button", { name: "Reactivar acceso" });
    await expect(reactivar).toBeVisible();

    await reactivar.click();
    await expect(page.getByText("Acceso reactivado")).toBeVisible();
    expect(llamadas.acceso).toEqual(["DELETE", "POST"]);
  });

  test("menú y links viejos llevan a Personas", async ({ page }) => {
    await mockPersonas(page);
    await page.goto("/admin/usuarios");
    await expect(page).toHaveURL(/\/personas$/);
    await expect(page.getByRole("link", { name: "Personas" }).first()).toBeVisible();

    await page.goto("/vacaciones/gestion?tab=empleados");
    await expect(page).toHaveURL(/\/personas$/);
  });
});
