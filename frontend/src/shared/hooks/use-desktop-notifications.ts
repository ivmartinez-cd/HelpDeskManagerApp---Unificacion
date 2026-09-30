"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/** Adapter único sobre la Web Notifications API del navegador — ningún otro
 * archivo del módulo debe tocar `Notification` directamente.
 *
 * La app puede servirse por HTTP plano en producción (sin TLS visible en
 * `docker-compose.yml`, `session_cookie_secure: bool = False` en el backend).
 * La Web Notifications API exige *secure context*: por HTTP, `window.Notification`
 * es directamente `undefined` (no "denegada"). Por eso el estado de soporte
 * distingue `unsupported` de `denied` — son causas distintas y requieren un
 * mensaje distinto para que el problema sea diagnosticable el día que alguien
 * lo vea en producción.
 */

const STORAGE_KEY = "insumos.notificaciones-escritorio";
const AUTO_CLOSE_MS = 15_000;

export type NotificationSupport = "unsupported" | "denied" | "granted" | "default";

export interface DesktopNotificationPayload {
  title: string;
  body: string;
  tag: string;
  url: string;
}

export interface DesktopNotificationsState {
  support: NotificationSupport;
  enabled: boolean;
  mounted: boolean;
  setEnabled: (value: boolean) => Promise<void>;
  notify: (payload: DesktopNotificationPayload) => void;
  /** Dispara una notificación de prueba independiente del toggle `enabled` —
   * para el botón "Probar notificación" del panel de diagnóstico. Devuelve
   * un mensaje humano listo para mostrar (éxito o motivo del fallo). */
  sendTestNotification: () => Promise<string>;
}

function detectSupport(): NotificationSupport {
  if (typeof window === "undefined" || typeof Notification === "undefined") return "unsupported";
  return Notification.permission;
}

function readStoredPreference(): boolean {
  // Storage bloqueado o corrupto: default `false`, no explota.
  try {
    return window.localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

function persistPreference(value: boolean): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, String(value));
  } catch {
    // Storage lleno o deshabilitado: la preferencia igual se aplica en memoria.
  }
}

export function useDesktopNotifications(
  onActivate?: (url: string) => void,
): DesktopNotificationsState {
  const [mounted, setMounted] = useState(false);
  const [support, setSupport] = useState<NotificationSupport>("unsupported");
  const [enabled, setEnabledState] = useState(false);
  const onActivateRef = useRef(onActivate);

  // El ref se sincroniza en un efecto propio, nunca durante el render (leer u
  // ordenar un `.current` fuera de un efecto/handler rompe la regla
  // `react-hooks/refs`).
  useEffect(() => {
    onActivateRef.current = onActivate;
  }, [onActivate]);

  // Sondeo de soporte y lectura de preferencia: recién en un efecto, nunca
  // durante el render (mismo patrón que `theme-toggle.tsx` — `Notification`
  // no existe en el servidor).
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- carga inicial, mismo patrón que theme-toggle
    setSupport(detectSupport());
    setEnabledState(readStoredPreference());
    setMounted(true);
  }, []);

  const setEnabled = useCallback(async (value: boolean) => {
    if (!value) {
      setEnabledState(false);
      persistPreference(false);
      return;
    }
    let currentSupport = detectSupport();
    if (currentSupport === "default") {
      // Tiene que llamarse dentro del handler del gesto del usuario: Chrome
      // rechaza `requestPermission()` si se dispara desde un efecto.
      const result = await Notification.requestPermission();
      currentSupport = result;
      setSupport(result);
    }
    const granted = currentSupport === "granted";
    setEnabledState(granted);
    persistPreference(granted);
  }, []);

  const sendTestNotification = useCallback(async (): Promise<string> => {
    if (detectSupport() === "unsupported") {
      return "El navegador no soporta notificaciones de escritorio.";
    }
    let currentSupport = detectSupport();
    if (currentSupport === "default") {
      const result = await Notification.requestPermission();
      currentSupport = result;
      setSupport(result);
    }
    if (currentSupport === "denied") {
      return "Las notificaciones están bloqueadas para este sitio en tu navegador.";
    }
    try {
      const n = new Notification("Prueba de notificaciones", {
        body: "Las notificaciones están configuradas correctamente en tu navegador.",
        icon: "/favicon.svg",
      });
      setTimeout(() => n.close(), AUTO_CLOSE_MS);
      return "Notificación de prueba enviada.";
    } catch (err) {
      return `Error al crear la notificación: ${(err as Error).message}`;
    }
  }, []);

  const notify = useCallback((payload: DesktopNotificationPayload) => {
    if (!enabled || support !== "granted") return;
    const n = new Notification(payload.title, {
      body: payload.body,
      tag: payload.tag,
      icon: "/favicon.svg",
    });
    setTimeout(() => n.close(), AUTO_CLOSE_MS);
    n.onclick = () => {
      window.focus();
      onActivateRef.current?.(payload.url);
      n.close();
    };
  }, [enabled, support]);

  return { support, enabled, mounted, setEnabled, notify, sendTestNotification };
}
