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

  test("debe mostrar el hub Centro de Contadores con las 8 herramientas al entrar sin ?tool=", async ({
    page,
  }) => {
    await page.goto("/contadores");

    await expect(page.getByRole("heading", { name: "Centro de Contadores" })).toBeVisible();

    // Cards del hub (título orientado a la acción, ver ToolDef.navLabel)
    await expect(page.getByRole("heading", { name: "Proyección Contadores" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Calculadora" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Procesar DB3" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Estimación en 0" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Suma Fija" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Descarga FTP" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Descargar SDS" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Descargar ERS" })).toBeVisible();
  });

  test("debe abrir el modal de una herramienta al entrar con ?tool= válido, sobre el hub", async ({
    page,
  }) => {
    await page.goto("/contadores?tool=proyeccion");

    await expect(page.getByRole("dialog", { name: "Proyección Contadores" })).toBeVisible();
    // El hub sigue montado detrás del modal.
    await expect(page.getByRole("heading", { name: "Centro de Contadores" })).toBeVisible();
  });

  test("debe cerrar el modal de una herramienta con Escape y volver al hub", async ({ page }) => {
    await page.goto("/contadores?tool=calc");

    await expect(page.getByRole("dialog", { name: "Calculadora" })).toBeVisible();

    await page.keyboard.press("Escape");

    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page).toHaveURL("/contadores");
  });

  test("debe calcular una estimación manual correctamente en la Calculadora", async ({ page }) => {
    // Nombres tal como los serializa el backend real (ver
    // manual_estimation_schemas.py, serialization_alias camelCase) — el
    // mock viejo usaba nombres snake_case que el backend nunca devolvió,
    // lo que ocultaba un crash real del panel de resultado (ver
    // ManualEstimationResponse en contadores-api.ts).
    await page.route("**/api/contadores/calc", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          impDia: 12.5,
          impMes: 375,
          diasEst: 5,
          impEst: 62,
          contEst: 562,
        }),
      });
    });

    await page.goto("/contadores?tool=calc");

    await page.getByPlaceholder("Ej: 10000").fill("10000");
    await page.getByPlaceholder("Ej: 15000").fill("15000");
    await page.getByLabel("Fecha Lectura Inicial").fill("2026-01-01");
    await page.getByLabel("Fecha Lectura Final").fill("2026-01-11");
    await page.getByLabel("Fecha Objetivo de Estimación").fill("2026-01-16");

    await page.getByRole("button", { name: "Calcular Estimación" }).click();

    await expect(page.getByText("562")).toBeVisible();
    await expect(page.getByText("5 días")).toBeVisible();
    await expect(page.getByText("12.50 / día")).toBeVisible();
  });

  test("debe elegir un cliente FTP en el modal de descarga y abrir la gestión de clientes", async ({
    page,
  }) => {
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

    // Modal combinado: selector de cliente + fecha + procesar.
    await expect(page.getByRole("dialog", { name: "Descarga FTP" })).toBeVisible();
    await expect(page.getByRole("option", { name: "CLIENTE TEST" })).toBeAttached();

    // "Gestionar clientes" abre un segundo modal con la lista completa.
    await page.getByRole("button", { name: "Gestionar clientes" }).click();
    await expect(page.getByRole("dialog", { name: "Clientes FTP" })).toBeVisible();
    await expect(page.getByText("CLIENTE TEST")).toBeVisible();
    await expect(page.getByText("ftp.test.com:21")).toBeVisible();

    await page.getByRole("button", { name: "Nuevo" }).click();
    await expect(page.getByRole("heading", { name: "Nuevo Cliente FTP" })).toBeVisible();
  });
});
