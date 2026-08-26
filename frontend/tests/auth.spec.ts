import { test, expect } from "./fixtures";

// Login (`/login`, fuera de `(app)`): ningún otro spec prueba el formulario
// real -- `global-setup.ts` mockea /api/auth/me y /api/auth/modules para que
// el resto de las pantallas arranque ya "logueado", así que este es el único
// lugar que ejercita `useLogin`/`LoginForm` de punta a punta.
test.describe("Login", () => {
  test("login exitoso redirige a Inicio @smoke", async ({ page }) => {
    await page.route("**/api/auth/login", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: "{}" }),
    );

    await page.goto("/login");
    await page.getByLabel("Usuario").fill("test@canaldirecto.com.ar");
    await page.getByLabel("Contraseña", { exact: true }).fill("password123");
    await page.getByRole("button", { name: "Ingresar" }).click();

    await expect(page).toHaveURL("/");
  });

  test("credenciales inválidas muestra el error del backend y no navega", async ({ page }) => {
    await page.route("**/api/auth/login", (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({
          message: "Usuario o contraseña incorrectos",
          code: "INVALID_CREDENTIALS",
        }),
      }),
    );

    await page.goto("/login");
    await page.getByLabel("Usuario").fill("test@canaldirecto.com.ar");
    await page.getByLabel("Contraseña", { exact: true }).fill("wrong-password");
    await page.getByRole("button", { name: "Ingresar" }).click();

    await expect(page.getByText("Usuario o contraseña incorrectos")).toBeVisible();
    await expect(page).toHaveURL("/login");
  });
});
