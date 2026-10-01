import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

// Tests unitarios de lógica pura (formato, fechas, permisos, validaciones):
// entorno node, sin DOM. Los flujos de pantalla los cubre Playwright (tests/).
export default defineConfig({
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  test: {
    environment: "node",
    // Los usuarios están en Argentina y varias funciones usan la fecha local:
    // los tests corren con esa zona aunque el contenedor esté en UTC.
    env: { TZ: "America/Argentina/Buenos_Aires" },
    include: ["src/**/*.test.ts"],
  },
});
