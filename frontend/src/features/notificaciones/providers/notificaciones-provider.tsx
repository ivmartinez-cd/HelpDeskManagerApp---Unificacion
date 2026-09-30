"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";
import {
  useDesktopNotifications,
  type DesktopNotificationsState,
} from "@/shared/hooks/use-desktop-notifications";
import { notificacionesApi, type Notificacion } from "../api/notificaciones-api";
import { useAvisosNuevos } from "../hooks/use-avisos-nuevos";
import { useNoLeidasPolling } from "../hooks/use-no-leidas-polling";

interface NotificacionesContextValue {
  /** No leídas del usuario: el badge de la campanita. */
  total: number;
  /** No leídas más recientes. Es un array nuevo en cada respuesta del
   * polling: la lista abierta de la campanita lo usa para releerse sola. */
  noLeidas: Notificacion[];
  /** Marca leída y navega a su `url` (si tiene). */
  abrir: (n: Notificacion) => void;
  marcarTodas: () => Promise<void>;
  escritorio: DesktopNotificationsState;
}

const NotificacionesContext = createContext<NotificacionesContextValue | null>(null);

/** Un solo poller por pestaña de la bandeja de notificaciones (campanita del
 * header). Vive en el layout de `(app)`, así los avisos llegan en cualquier
 * pantalla. Qué notificaciones ve cada uno lo decide el backend según sus
 * funciones y permisos. */
export function NotificacionesProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { noLeidas, total, cargado, refetch } = useNoLeidasPolling();
  const navegar = useCallback((url: string) => router.push(url), [router]);
  const escritorio = useDesktopNotifications(navegar);

  const abrir = useCallback(
    (n: Notificacion) => {
      if (!n.leida) {
        notificacionesApi
          .marcarLeidas([n.id])
          .then(refetch)
          .catch((err: unknown) => console.error("Error al marcar la notificación:", err));
      }
      if (n.url) router.push(n.url);
    },
    [router, refetch],
  );

  const marcarTodas = useCallback(async () => {
    await notificacionesApi.marcarLeidas();
    refetch();
  }, [refetch]);

  useAvisosNuevos(noLeidas, cargado, abrir, escritorio.notify);

  const value = useMemo(
    () => ({ total, noLeidas, abrir, marcarTodas, escritorio }),
    [total, noLeidas, abrir, marcarTodas, escritorio],
  );
  return <NotificacionesContext.Provider value={value}>{children}</NotificacionesContext.Provider>;
}

export function useNotificaciones(): NotificacionesContextValue {
  const ctx = useContext(NotificacionesContext);
  if (!ctx) throw new Error("useNotificaciones fuera de NotificacionesProvider");
  return ctx;
}
