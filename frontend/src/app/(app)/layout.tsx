import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import type { IdentityResponse, ModuleSummary } from "@/features/auth/api/auth-api";
import { Sidebar } from "@/shared/components/sidebar";
import { SessionProvider } from "@/services/session-provider";

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8012";

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
    (await fetchFromBackend<ModuleSummary[]>("/api/auth/modules", cookieHeader)) ?? [];

  return (
    <SessionProvider user={identity.user} permissions={identity.permissions} modules={modules}>
      <Sidebar>{children}</Sidebar>
    </SessionProvider>
  );
}
