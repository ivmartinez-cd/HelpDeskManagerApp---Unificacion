import { expect, test } from "./fixtures";

test.describe("Módulo de Contadores - Interfaz y Herramientas", () => {
  test("debe mostrar el hub Centro de Contadores con las 7 herramientas al entrar sin ?tool= @smoke", async ({
    page,
  }) => {
    await page.goto("/contadores");

    await expect(page.getByRole("heading", { name: "Centro de Contadores" })).toBeVisible();

    // Cards del hub (título orientado a la acción, ver ToolDef.navLabel). El
    // Calendario ya no es una card del hub: vive en /contadores/calendario
    // (commit f685707, "sacar card Calendario de Rutas del hub").
    await expect(page.getByRole("heading", { name: "Calendario de Rutas" })).toHaveCount(0);
    await expect(page.getByRole("heading", { name: "Proyección Contadores" })).toBeVisible();
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
    await page.goto("/contadores?tool=db3");

    await expect(page.getByRole("dialog", { name: "Procesar DB3" })).toBeVisible();
    // El hub sigue montado detrás del modal.
    await expect(page.getByRole("heading", { name: "Centro de Contadores" })).toBeVisible();
  });

  test("debe cerrar el modal de una herramienta con el botón X y volver al hub", async ({ page }) => {
    await page.goto("/contadores?tool=db3");

    await expect(page.getByRole("dialog", { name: "Procesar DB3" })).toBeVisible();

    await page.getByRole("button", { name: "Cerrar modal" }).click();

    // BrandModal se desmonta cuando la URL cambia (ToolLauncherModal retorna null con tool=null)
    await expect(page).toHaveURL("/contadores");
    await expect(page.getByRole("dialog", { name: "Procesar DB3" })).not.toBeVisible();
  });

  test("debe mostrar el formulario de Procesar DB3 con input de archivo y botón de envío", async ({
    page,
  }) => {
    await page.goto("/contadores?tool=db3");

    await expect(page.getByRole("dialog", { name: "Procesar DB3" })).toBeVisible();
    await expect(page.getByLabel("Archivos SQLite (.db3)")).toBeVisible();
    await expect(page.getByLabel("Fecha Máxima de Lectura (Opcional)")).toBeVisible();
    await expect(page.getByRole("button", { name: "Procesar DB3 a CSV" })).toBeVisible();
  });

  test("debe elegir un cliente FTP en el modal de descarga y abrir la gestión de clientes", async ({
    page,
  }) => {
    // listFtpClients espera Page<FtpClient> — devuelve page.items al componente
    await page.route("**/api/contadores/ftp/clients", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
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
          ],
          total: 1,
          page: 1,
          size: 50,
        }),
      });
    });

    await page.goto("/contadores?tool=ftp");

    // Modal combinado: selector de cliente + fecha + procesar.
    await expect(page.getByRole("dialog", { name: "Descarga FTP" })).toBeVisible();

    // Esperar que carguen los clientes (el trigger pasa de "Cargando clientes..." al placeholder)
    const trigger = page.getByRole("button", { name: "Seleccionar cliente FTP" });
    await expect(trigger).toBeVisible();

    // Abrir el dropdown para ver los options
    await trigger.click();
    await expect(page.getByRole("option", { name: "CLIENTE TEST" })).toBeVisible();

    // "Gestionar clientes" abre un segundo modal con la lista completa.
    await page.getByRole("button", { name: "Gestionar clientes" }).click();
    await expect(page.getByRole("dialog", { name: "Clientes FTP" })).toBeVisible();
    await expect(page.getByText("CLIENTE TEST")).toBeVisible();
    // El componente muestra client.host en la columna Servidor (no host:port)
    await expect(page.getByText("ftp.test.com")).toBeVisible();

    await page.getByRole("button", { name: "Nuevo", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Nuevo Cliente FTP" })).toBeVisible();
  });
});
