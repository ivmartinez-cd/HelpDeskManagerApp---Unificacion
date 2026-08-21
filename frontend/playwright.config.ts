import { defineConfig, devices } from "@playwright/test";

// Override BACKEND_URL para que el webServer (Next.js local) use el mock backend
// en vez del backend real de Docker. El mock responde /api/auth/me y /api/auth/modules.
process.env.BACKEND_URL = "http://127.0.0.1:18099";
// URL de prueba (dominio reservado para testing, RFC 2606) para que
// inicio.spec.ts pueda verificar el ícono de WATI del header -- sin esto
// WATI_URL queda sin setear y el ícono nunca se renderiza (ver layout.tsx).
process.env.WATI_URL = "https://wati.example.test/inbox";

// Puerto del Next.js de test: 3001 por defecto; `PW_PORT` permite correr en otro
// cuando 3001 está ocupado en la máquina (p. ej. por otro contenedor).
const PORT = process.env.PW_PORT ?? "3001";

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
    baseURL: `http://localhost:${PORT}`,
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: `npx next dev --turbopack -p ${PORT}`,
    // /login es ruta pública (sin layout de auth) — el health check de Playwright
    // ocurre antes del globalSetup, así que no debe pasar por el layout de app
    // o generaría un redirect cacheado antes de que el mock backend esté listo.
    url: `http://localhost:${PORT}/login`,
    timeout: 120_000,
    reuseExistingServer: !process.env.CI,
    stdout: "pipe",
    stderr: "pipe",
  },
});
