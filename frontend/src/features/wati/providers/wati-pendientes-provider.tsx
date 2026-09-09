"use client";

import { createContext, useContext, type ReactNode } from "react";
import { useSession } from "@/services/session-provider";
import { WatiAvisosModal } from "../components/wati-avisos-modal";
import { useTurnoSt, type TurnoStState } from "../hooks/use-turno-st";
import { useWatiAvisos, type WatiAvisosState } from "../hooks/use-wati-alertas";
import { useWatiPendientesPolling, type WatiPendientesState } from "../hooks/use-wati-pendientes";

interface WatiPendientesContextValue extends WatiPendientesState, TurnoStState, WatiAvisosState {
  /** false si el usuario no tiene el módulo wati: nada se consulta ni se avisa. */
  habilitado: boolean;
  /** Inbox de WATI: la que informa el backend o, si no, `WATI_URL` del entorno. */
  inboxUrl: string | null;
}

const DESHABILITADO: WatiPendientesContextValue = {
  habilitado: false,
  inboxUrl: null,
  resumen: null,
  pendientes: [],
  loading: false,
  error: null,
  refetch: () => undefined,
  enHorarioSt: false,
  soyOperadorSt: false,
  avisos: [],
  confirmar: () => undefined,
};

const WatiPendientesContext = createContext<WatiPendientesContextValue>(DESHABILITADO);

/** Un solo poller por pestaña para todo lo que muestra chats de WhatsApp
 * pendientes (badge del header, banner personal, card de Inicio, pantalla
 * /wati) y un solo lector de turnos para saber si es horario de ST y si el
 * usuario logueado es quien lo cubre. Los avisos por umbral (toast a los
 * 15 min, modal bloqueante a la hora, con sonido; ADR-036) se disparan solo
 * para ese operador. Vive en
 * el layout de `(app)`, así los avisos llegan en cualquier módulo. */
export function WatiPendientesProvider({
  watiUrl,
  children,
}: {
  watiUrl: string | null;
  children: ReactNode;
}) {
  const { user, modules } = useSession();
  const habilitado = modules.some((m) => m.key === "wati");
  const estado = useWatiPendientesPolling(habilitado);
  const turno = useTurnoSt(habilitado, user.id);
  const inboxUrl = estado.resumen?.inbox_url ?? watiUrl;
  const avisos = useWatiAvisos(estado.pendientes, habilitado && turno.soyOperadorSt, inboxUrl);
  return (
    <WatiPendientesContext.Provider value={{ habilitado, inboxUrl, ...estado, ...turno, ...avisos }}>
      {children}
      <WatiAvisosModal avisos={avisos.avisos} confirmar={avisos.confirmar} inboxUrl={inboxUrl} />
    </WatiPendientesContext.Provider>
  );
}

export function useWatiPendientes(): WatiPendientesContextValue {
  return useContext(WatiPendientesContext);
}
