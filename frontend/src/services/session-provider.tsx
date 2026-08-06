"use client";

import { createContext, useContext, type ReactNode } from "react";
import type { ModuleSummary, PermissionSummary, UserSummary } from "@/features/auth/api/auth-api";

interface SessionContextValue {
  user: UserSummary;
  permissions: PermissionSummary[];
  modules: ModuleSummary[];
  can: (module: string, action: string) => boolean;
}

const SessionContext = createContext<SessionContextValue | null>(null);

interface SessionProviderProps {
  user: UserSummary;
  permissions: PermissionSummary[];
  modules: ModuleSummary[];
  children: ReactNode;
}

export function SessionProvider({ user, permissions, modules, children }: SessionProviderProps) {
  function can(module: string, action: string): boolean {
    return permissions.some((p) => p.module === module && p.action === action);
  }

  return (
    <SessionContext.Provider value={{ user, permissions, modules, can }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession debe usarse dentro de <SessionProvider>");
  }
  return context;
}
