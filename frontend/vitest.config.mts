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
    include: ["src/**/*.test.ts"],
  },
});
