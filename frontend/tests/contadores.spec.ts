import { expect, test } from "@playwright/test";

test.describe("Módulo de Contadores - Interfaz y Herramientas", () => {
  test.beforeEach(async ({ page, context }) => {
    // Inyectar cookie de sesión o interceptar /api/auth/me para permitir acceso directo
    await context.addCookies([
      {
        name: "hdm_session",
        value: "mock-session-token",
        domain: "localhost",
        path: "/",
      },
    ]);

    await page.route("**/api/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user: {
            id: "00000000-0000-0000-0000-000000000001",
            email: "admin@canaldirecto.com.ar",
            fullName: "Administrador",
            isActive: true,
            isSuperadmin: true,
          },
          permissions: [{ moduleKey: "contadores", actionKey: "export" }],
        }),
      });
    });

    await page.route("**/api/auth/modules", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            key: "contadores",
            label: "Contadores",
            route: "/contadores",
            icon: "printer",
            sortOrder: 5,
            isEnabled: true,
          },
        ]),
      });
    });
  });

  test("debe cargar la página principal de contadores con las 8 pestañas de herramientas", async ({
    page,
  }) => {
    await page.goto("/contadores");

    await expect(page.getByRole("heading", { name: "Módulo de Contadores" })).toBeVisible();

    // Pestañas
    await expect(page.getByRole("button", { name: "Proyección" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Calculadora" })).toBeVisible();
    await expect(page.getByRole("button", { name: "DB3 a CSV" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Estimación en 0" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Suma Fija" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Clientes FTP" })).toBeVisible();
    await expect(page.getByRole("button", { name: "HP SDS" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Epson ERS" })).toBeVisible();
  });

  test("debe permitir cambiar entre pestañas de herramientas", async ({ page }) => {
    await page.goto("/contadores");

    // Click en Calculadora
    await page.getByRole("button", { name: "Calculadora" }).click();
    await expect(page.getByRole("heading", { name: "Datos para la Estimación Manual" })).toBeVisible();

    // Click en DB3 a CSV
    await page.getByRole("button", { name: "DB3 a CSV" }).click();
    await expect(page.getByRole("heading", { name: "Consolidación de Archivos DB3 a CSV" })).toBeVisible();

    // Click en Clientes FTP
    await page.getByRole("button", { name: "Clientes FTP" }).click();
    await expect(page.getByRole("button", { name: "Nuevo Cliente FTP" })).toBeVisible();
  });

  test("debe calcular una estimación manual correctamente en la Calculadora", async ({ page }) => {
    await page.route("**/api/contadores/calc", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          dias_muestra: 10,
          consumo_muestra: 5000,
          consumo_diario: 500,
          dias_estimados: 5,
          contador_estimado: 17500,
        }),
      });
    });

    await page.goto("/contadores?tool=calc");

    await page.getByPlaceholder("Ej: 10000").fill("10000");
    await page.getByPlaceholder("Ej: 15000").fill("15000");
    await page.locator('input[type="date"]').nth(0).fill("2026-01-01");
    await page.locator('input[type="date"]').nth(1).fill("2026-01-11");
    await page.locator('input[type="date"]').nth(2).fill("2026-01-16");

    await page.getByRole("button", { name: "Calcular Estimación" }).click();

    await expect(page.getByText("17.500")).toBeVisible();
    await expect(page.getByText("10 días")).toBeVisible();
    await expect(page.getByText("500.00 / día")).toBeVisible();
  });

  test("debe listar clientes FTP y abrir modal para nuevo cliente", async ({ page }) => {
    await page.route("**/api/contadores/ftp/clients", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: "ftp-1",
            name: "CLIENTE TEST",
            host: "ftp.test.com",
            port: 21,
            username: "user_test",
            remote_dir: "/",
            created_at: "2026-08-07",
            updated_at: "2026-08-07",
          },
        ]),
      });
    });

    await page.goto("/contadores?tool=ftp");

    await expect(page.getByText("CLIENTE TEST")).toBeVisible();
    await expect(page.getByText("ftp.test.com:21")).toBeVisible();

    await page.getByRole("button", { name: "Nuevo Cliente FTP" }).click();
    await expect(page.getByRole("heading", { name: "Nuevo Cliente FTP" })).toBeVisible();
  });
});
