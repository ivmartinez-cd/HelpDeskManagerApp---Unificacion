import * as http from "http";
import type { IncomingMessage, ServerResponse } from "http";

const USER_MOCK = {
  user: {
    id: "00000000-0000-0000-0000-000000000001",
    email: "test@canaldirecto.com.ar",
    fullName: "Test Admin",
    isActive: true,
    isSuperadmin: true,
  },
  permissions: [
    { moduleKey: "liquidaciones", actionKey: "view" },
    { moduleKey: "liquidaciones", actionKey: "create" },
    { moduleKey: "liquidaciones", actionKey: "update" },
    { moduleKey: "contadores", actionKey: "export" },
    { moduleKey: "vacaciones", actionKey: "view" },
    { moduleKey: "vacaciones", actionKey: "create" },
    { moduleKey: "vacaciones", actionKey: "approve" },
    { moduleKey: "vacaciones", actionKey: "manage" },
    { moduleKey: "analisis-log-hp", actionKey: "view" },
    { moduleKey: "analisis-log-hp", actionKey: "export" },
  ],
};

// Catálogo real (ver `module` en la DB) -- completo, no solo los módulos que
// algún spec toca puntualmente: componentes de otras pantallas (ej. el botón
// "Sincronizar desde Siges" de prestadores) también leen `useSession().modules`.
const MODULES_MOCK = [
  {
    key: "contadores",
    label: "Contadores",
    route: "/contadores",
    icon: "printer",
    sortOrder: 5,
    isEnabled: true,
  },
  {
    key: "insumos",
    label: "Insumos",
    route: "/insumos",
    icon: "package",
    sortOrder: 10,
    isEnabled: true,
  },
  {
    key: "sla",
    label: "SLA",
    route: "/sla",
    icon: "gauge",
    sortOrder: 15,
    isEnabled: true,
  },
  {
    key: "prestadores",
    label: "Prestadores",
    route: "/prestadores",
    icon: "wrench",
    sortOrder: 18,
    isEnabled: true,
  },
  {
    key: "liquidaciones",
    label: "Liquidaciones",
    route: "/liquidaciones",
    icon: "invoice",
    sortOrder: 20,
    isEnabled: true,
  },
  {
    key: "vacaciones",
    label: "Gestión de Personal",
    route: "/vacaciones",
    icon: "calendar",
    sortOrder: 30,
    isEnabled: true,
  },
  {
    key: "analisis-log-hp",
    label: "Análisis de Log HP",
    route: "/analisis-log-hp",
    icon: "printer",
    sortOrder: 40,
    isEnabled: true,
  },
  {
    key: "preventivos",
    label: "Preventivos",
    route: "/preventivos",
    icon: "calendar-clock",
    sortOrder: 45,
    isEnabled: true,
  },
];

function handler(req: IncomingMessage, res: ServerResponse) {
  const url = (req.url ?? "/").split("?")[0];
  console.log(`[mock-backend] ${req.method} ${url}`);

  if (url === "/api/auth/me") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(USER_MOCK));
  } else if (url === "/api/auth/modules") {
    // Envelope Page[T] real (ver src/shared/presentation/schemas/pagination.py)
    // -- un array pelado dejaba `modules` siempre en [] en app/(app)/layout.tsx
    // (`.items ?? []`), sin que ningún spec existente lo notara porque
    // ninguno depende de useSession().modules para su propio contenido.
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({ items: MODULES_MOCK, total: MODULES_MOCK.length, page: 1, size: 200 }),
    );
  } else {
    // Devolver 404 para todo lo demás (los datos de negocio los mockea page.route())
    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ detail: "Not found by mock backend" }));
  }
}

export default async function globalSetup() {
  const server = http.createServer(handler);
  await new Promise<void>((resolve) => server.listen(18099, "127.0.0.1", () => resolve()));
  console.log("[mock-backend] Listening on http://127.0.0.1:18099");
  // Guardado en global para que globalTeardown pueda cerrarlo (mismo proceso)
  (global as Record<string, unknown>).__PLAYWRIGHT_MOCK_BACKEND__ = server;
}
