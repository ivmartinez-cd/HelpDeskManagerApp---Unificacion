"use client";

import { createContext, useContext, type ReactNode } from "react";
import { useSession } from "@/services/session-provider";
import { useModificacionesAvisos } from "../hooks/use-modificaciones-avisos";
import { useModificacionesPolling } from "../hooks/use-modificaciones-polling";

interface ModificacionesContextValue {
  /** false si el usuario no tiene el módulo liquidaciones: nada se consulta. */
  habilitado: boolean;
  /** Modificaciones del prestador sin ver, de todas las liquidaciones. */
  total: number;
}

const DESHABILITADO: ModificacionesContextValue = { habilitado: false, total: 0 };

const ModificacionesContext = createContext<ModificacionesContextValue>(DESHABILITADO);

/** Un solo poller por pestaña de modificaciones del prestador sin ver (ADR-038):
 * alimenta el badge del ítem "Liquidaciones" del menú y dispara un toast
 * persistente con sonido por liquidación, en cualquier pantalla — vive en el
 * layout de `(app)`, igual que `WatiPendientesProvider`. */
export function ModificacionesProvider({ children }: { children: ReactNode }) {
  const { modules } = useSession();
  const habilitado = modules.some((m) => m.key === "liquidaciones");
  const { noVistas, total } = useModificacionesPolling(habilitado);
  useModificacionesAvisos(noVistas, habilitado);

  return (
    <ModificacionesContext.Provider value={{ habilitado, total }}>
      {children}
    </ModificacionesContext.Provider>
  );
}

export function useModificacionesPrestador(): ModificacionesContextValue {
  return useContext(ModificacionesContext);
}
