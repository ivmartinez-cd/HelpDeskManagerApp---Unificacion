import { defineConfig, devices } from "@playwright/test";

// Override BACKEND_URL para que el webServer (Next.js local) use el mock backend
// en vez del backend real de Docker. El mock responde /api/auth/me y /api/auth/modules.
process.env.BACKEND_URL = "http://127.0.0.1:18099";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: "list",
  globalSetup: "./tests/global-setup",
  globalTeardown: "./tests/global-teardown",
  use: {
    baseURL: "http://localhost:3001",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npx next dev --turbopack -p 3001",
    // /login es ruta pública (sin layout de auth) — el health check de Playwright
    // ocurre antes del globalSetup, así que no debe pasar por el layout de app
    // o generaría un redirect cacheado antes de que el mock backend esté listo.
    url: "http://localhost:3001/login",
    timeout: 120_000,
    reuseExistingServer: !process.env.CI,
    stdout: "pipe",
    stderr: "pipe",
  },
});
