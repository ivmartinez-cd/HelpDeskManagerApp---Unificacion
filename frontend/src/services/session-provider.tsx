"use client";

import { createContext, useContext, type ReactNode } from "react";
import type { ModuleSummary, PermissionSummary, UserSummary } from "@/features/auth/api/auth-api";

interface SessionContextValue {
  user: UserSummary;
  permissions: PermissionSummary[];
  /** Funciones (pantallas/cards) concedidas, por clave (ADR-032). */
  features: string[];
  modules: ModuleSummary[];
  can: (module: string, action: string) => boolean;
  /** ¿Tiene la función (pantalla/card) concedida? Superadmin: siempre. */
  hasFeature: (feature: string) => boolean;
}

const SessionContext = createContext<SessionContextValue | null>(null);

interface SessionProviderProps {
  user: UserSummary;
  permissions: PermissionSummary[];
  features?: string[];
  modules: ModuleSummary[];
  children: ReactNode;
}

export function SessionProvider({
  user,
  permissions,
  features = [],
  modules,
  children,
}: SessionProviderProps) {
  function can(module: string, action: string): boolean {
    if (user.isSuperadmin) return true;
    return permissions.some((p) => p.module === module && p.action === action);
  }

  function hasFeature(feature: string): boolean {
    if (user.isSuperadmin) return true;
    return features.includes(feature);
  }

  return (
    <SessionContext.Provider value={{ user, permissions, features, modules, can, hasFeature }}>
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
