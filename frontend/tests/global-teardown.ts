import * as http from "http";

export default async function globalTeardown() {
  const server = (global as Record<string, unknown>).__PLAYWRIGHT_MOCK_BACKEND__ as
    | http.Server
    | undefined;
  if (server) {
    await new Promise<void>((resolve) => server.close(() => resolve()));
    console.log("[mock-backend] Stopped");
  }
}
