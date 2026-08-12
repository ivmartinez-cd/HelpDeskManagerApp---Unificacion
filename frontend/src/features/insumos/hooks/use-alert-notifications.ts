"use client";

import { useEffect, useRef } from "react";
import type { ClassifiedAlert } from "./use-request-alerts";
import type { DesktopNotificationPayload } from "./use-desktop-notifications";

/** Traduce las alertas clasificadas de `useRequestAlerts` (dato + severidad)
 * a notificaciones de escritorio (I/O de navegador). Separado a propósito de
 * `use-request-alerts.ts`: mezclar ambas cosas viola responsabilidad única y
 * vuelve imposible testear el I/O del navegador en aislamiento.
 */

const ALERT_TAG = "insumos-alertas";

export function useAlertNotifications(
  alerts: readonly ClassifiedAlert[],
  notify: (payload: DesktopNotificationPayload) => void,
): void {
  // Set de ids ya notificados. SIEMPRE ref, nunca state: escribir estado desde
  // el efecto de polling re-renderiza el Dashboard cada 60s sin necesidad
  // (regla del lint `react-hooks/set-state-in-effect`).
  const seenRef = useRef<Set<number>>(new Set());
  const firstRunRef = useRef(true);

  useEffect(() => {
    if (alerts.length === 0) return;

    // Primera carga: sembrar el set de "ya vistos" con lo que ya está
    // pendiente sin notificar nada, si no cada apertura de página notificaría
    // de golpe todo lo acumulado.
    if (firstRunRef.current) {
      firstRunRef.current = false;
      for (const alert of alerts) seenRef.current.add(alert.hpRequestId);
      return;
    }

    const fresh = alerts.filter((alert) => !seenRef.current.has(alert.hpRequestId));
    // El set es monotónico: solo se agregan ids, nunca se sacan (si no, una
    // alerta que aparece/desaparece/reaparece notificaría dos veces).
    for (const alert of fresh) seenRef.current.add(alert.hpRequestId);
    if (fresh.length === 0) return;

    notify(buildPayload(fresh));
  }, [alerts, notify]);
}

function buildPayload(fresh: readonly ClassifiedAlert[]): DesktopNotificationPayload {
  const customerIds = new Set(fresh.map((alert) => alert.customerId ?? null));
  const sameCustomer = customerIds.size === 1 ? fresh[0].customerId : null;
  const url = sameCustomer ? `/insumos?customerId=${sameCustomer}` : "/insumos";

  if (fresh.length === 1) {
    const alert = fresh[0];
    return {
      title: "Solicitud de insumo sin cargar",
      body: `${alert.customerName} — ${alert.description}`,
      tag: ALERT_TAG,
      url,
    };
  }

  return {
    title: `${fresh.length} solicitudes nuevas sin cargar`,
    body: sameCustomer ? fresh[0].customerName : "Varios clientes",
    tag: ALERT_TAG,
    url,
  };
}
