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

// La máquina de desarrollo tiene proxy HTTP corporativo por variables de entorno
// (http_proxy/https_proxy); Chromium las hereda y manda http://localhost:PORT al
// proxy, que lo rechaza (todas las navegaciones terminan en net::ERR_ABORTED).
// Un `no_proxy` con `<local>` no alcanza para Chromium en Linux. Los tests solo
// hablan con localhost (Next de prueba + mock backend), así que se quitan acá
// para el webServer y el navegador lanzado por Playwright.
for (const key of ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"]) {
  delete process.env[key];
}

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: "list",
  // Filesystem lento en WSL (mismo motivo que el timeout de 300s del webServer
  // más abajo): Turbopack recompila cada ruta la primera vez que un test la
  // visita en el proceso de `next dev` recién levantado, y esa primera
  // compilación puede superar el default de 30s -- se vio de forma reproducible
  // en vacaciones.spec.ts (7-8 rutas propias) con `page.goto` fallando por
  // net::ERR_ABORTED aun sin otra carga en la máquina.
  //
  // TODO (retomar 2026-08-26 ~17hs): con este timeout en 60s y la máquina sin
  // otra carga, la suite completa corre limpia salvo por rutas de
  // vacaciones.spec.ts que dependen de /vacaciones/asistencias -- ese caso no
  // es cuestión de tiempo: en el log del webServer aparece
  // "○ Compiling /vacaciones/asistencias ..." y nunca llega a imprimir el
  // "GET ... 200 in Xs" correspondiente (a diferencia de todas las demás
  // rutas del mismo módulo, incluida /vacaciones/reportes que sí terminó en
  // 13s). Es Turbopack colgado compilando esa ruta puntual, no lentitud —
  // los componentes de asistencias-view no tienen imports pesados (sin
  // chart.js/leaflet), así que no es peso de bundle. Subir el timeout no lo
  // arregla de fondo. Opciones evaluadas, sin implementar todavía:
  //   1. `retries: 1` también fuera de CI (hoy solo en CI) -- mitiga el
  //      cuelgue puntual sin tocar nada más, bajo esfuerzo.
  //   2. Sacar `--turbopack` del comando del webServer de test (volver a
  //      webpack) -- compila más lento en general pero evita este tipo de
  //      cuelgues; falta medir el impacto en el tiempo total de la suite.
  timeout: 60_000,
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
    // Filesystem lento en WSL: el primer compile de /login puede pasar los 2 min.
    timeout: 300_000,
    reuseExistingServer: !process.env.CI,
    stdout: "pipe",
    stderr: "pipe",
  },
});
