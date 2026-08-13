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
  ],
};

const MODULES_MOCK = [
  {
    key: "liquidaciones",
    label: "Liquidaciones",
    route: "/liquidaciones",
    icon: "invoice",
    sortOrder: 4,
    isEnabled: true,
  },
  {
    key: "contadores",
    label: "Contadores",
    route: "/contadores",
    icon: "printer",
    sortOrder: 5,
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
];

function handler(req: IncomingMessage, res: ServerResponse) {
  const url = (req.url ?? "/").split("?")[0];
  console.log(`[mock-backend] ${req.method} ${url}`);

  if (url === "/api/auth/me") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(USER_MOCK));
  } else if (url === "/api/auth/modules") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(MODULES_MOCK));
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
