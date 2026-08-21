import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import type { IdentityResponse, ModuleSummary, Page } from "@/features/auth/api/auth-api";
import { RouteTracker } from "@/shared/components/route-tracker";
import { Sidebar } from "@/shared/components/sidebar";
import { SessionProvider } from "@/services/session-provider";

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8012";
// Server-side (no NEXT_PUBLIC_*): el contenedor de frontend corre
// `next build && next start` (ver CLAUDE.md, sin hot reload), así que una
// NEXT_PUBLIC_ quedaría horneada en el build y cambiarla exigiría rebuild
// completo. Leída acá, alcanza con editar .env y recrear el contenedor.
const WATI_URL = process.env.WATI_URL || null;

async function fetchFromBackend<T>(path: string, cookieHeader: string): Promise<T | null> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    headers: { cookie: cookieHeader },
    cache: "no-store",
  });
  if (!response.ok) return null;
  return (await response.json()) as T;
}

export default async function AppLayout({ children }: { children: ReactNode }) {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();

  // El backend, no el proxy.ts, decide si la sesión sigue siendo válida —
  // el proxy solo mira si la cookie existe (chequeo barato, ver src/proxy.ts).
  const identity = await fetchFromBackend<IdentityResponse>("/api/auth/me", cookieHeader);
  if (!identity) {
    redirect("/login");
  }
  const modules =
    (await fetchFromBackend<Page<ModuleSummary>>("/api/auth/modules", cookieHeader))?.items ?? [];

  return (
    <SessionProvider user={identity.user} permissions={identity.permissions} modules={modules}>
      <RouteTracker />
      <Sidebar watiUrl={WATI_URL}>{children}</Sidebar>
    </SessionProvider>
  );
}
