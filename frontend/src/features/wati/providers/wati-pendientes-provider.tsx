"use client";

import { createContext, useContext, type ReactNode } from "react";
import { useSession } from "@/services/session-provider";
import { useWatiAlertas } from "../hooks/use-wati-alertas";
import { useWatiPendientesPolling, type WatiPendientesState } from "../hooks/use-wati-pendientes";

interface WatiPendientesContextValue extends WatiPendientesState {
  /** false si el usuario no tiene el módulo wati: nada se consulta ni se avisa. */
  habilitado: boolean;
}

const DESHABILITADO: WatiPendientesContextValue = {
  habilitado: false,
  resumen: null,
  pendientes: [],
  loading: false,
  error: null,
  refetch: () => undefined,
};

const WatiPendientesContext = createContext<WatiPendientesContextValue>(DESHABILITADO);

/** Un solo poller por pestaña para todo lo que muestra chats de WhatsApp
 * pendientes (badge del header, banner personal, card de Inicio, pantalla
 * /wati) y el disparo de avisos por umbral. Vive en el layout de `(app)`,
 * así los avisos llegan en cualquier módulo, no solo en Inicio. */
export function WatiPendientesProvider({ children }: { children: ReactNode }) {
  const { modules } = useSession();
  const habilitado = modules.some((m) => m.key === "wati");
  const estado = useWatiPendientesPolling(habilitado);
  useWatiAlertas(estado.pendientes, estado.resumen?.inbox_url ?? null);
  return (
    <WatiPendientesContext.Provider value={{ habilitado, ...estado }}>
      {children}
    </WatiPendientesContext.Provider>
  );
}

export function useWatiPendientes(): WatiPendientesContextValue {
  return useContext(WatiPendientesContext);
}
