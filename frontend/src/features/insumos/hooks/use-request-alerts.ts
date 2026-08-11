"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { insumosApi } from "../api/insumos-api";
import type { AlertRow } from "../types";

/** Alertas escaladas de solicitudes sin cargar (`GET /api/insumos/alerts`).
 *
 * **Mapeo de severidad**: el backend NO devuelve un nivel. `/alerts` ya
 * devuelve solo lo escalado y sin reconocer (`request_alerts` en estado
 * ESCALATED), así que las tres bandas visuales del Patrón 3 se derivan de la
 * antigüedad — que es el criterio con el que el backend decide escalar en
 * primer lugar (`alert_escalation.py`: el umbral se mide contra `requestedAt`,
 * "lo que importa es hace cuánto espera el cliente"):
 *
 *  - **Crítico** (rojo, siempre expandido): ≥ 24 h esperando.
 *  - **Advertencia** (amarillo, colapsable): ≥ 8 h (una jornada laboral).
 *  - **Informativo** (gris, colapsable): recién escalada, < 8 h.
 *
 * La base de la cuenta es `requestedAt`; si HP no lo mandó se cae a
 * `firstSeenAt` (cuándo la vio esta app por primera vez).
 */

const CRITICAL_HOURS = 24;
const WARNING_HOURS = 8;
const POLL_INTERVAL_MS = 60_000;

export type AlertSeverity = "critical" | "warning" | "info";

export interface ClassifiedAlert extends AlertRow {
  severity: AlertSeverity;
  /** Horas transcurridas desde que HP pidió el insumo. */
  ageHours: number;
}

function ageInHours(alert: AlertRow, nowMs: number): number {
  const reference = alert.requestedAt ?? alert.firstSeenAt;
  const referenceMs = new Date(reference).getTime();
  if (Number.isNaN(referenceMs)) return 0;
  return Math.max(0, (nowMs - referenceMs) / 3_600_000);
}

function severityFor(ageHours: number): AlertSeverity {
  if (ageHours >= CRITICAL_HOURS) return "critical";
  if (ageHours >= WARNING_HOURS) return "warning";
  return "info";
}

export interface RequestAlertsState {
  alerts: ClassifiedAlert[];
  bySeverity: Record<AlertSeverity, ClassifiedAlert[]>;
  total: number;
  loading: boolean;
  error: string | null;
  acknowledging: boolean;
  refresh: () => Promise<void>;
  acknowledge: (hpRequestIds: number[]) => Promise<void>;
}

export function useRequestAlerts(): RequestAlertsState {
  const [rows, setRows] = useState<AlertRow[]>([]);
  // Momento en que llegó el listado: la antigüedad (y por lo tanto la
  // severidad) se calcula contra este valor, no contra `Date.now()` durante el
  // render — un render tiene que ser puro, y de paso las bandas solo se
  // recalculan cuando hay datos nuevos (cada 60s).
  const [fetchedAtMs, setFetchedAtMs] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acknowledging, setAcknowledging] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const page = await insumosApi.listAlerts();
      setRows(page.items);
      setFetchedAtMs(Date.now());
      // El `total` del envelope es el `escalatedCount` del legacy: puede ser
      // mayor que `items.length` si hay más alertas que el `size` pedido.
      setTotal(page.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // El primer tick sale por microtask y no en el cuerpo del efecto: `refresh`
    // solo escribe estado después del `await`, pero el linter de React no puede
    // demostrarlo y lo cuenta como setState sincrónico dentro del efecto.
    queueMicrotask(() => void refresh());
    const handle = setInterval(() => void refresh(), POLL_INTERVAL_MS);
    return () => clearInterval(handle);
  }, [refresh]);

  const acknowledge = useCallback(
    async (hpRequestIds: number[]) => {
      if (hpRequestIds.length === 0) return;
      setAcknowledging(true);
      try {
        const response = await insumosApi.acknowledgeAlerts(hpRequestIds);
        if (!response.ok) {
          toast.error("No se pudieron reconocer las alertas");
          return;
        }
        toast.success(`${response.acknowledged} alerta(s) reconocida(s)`);
        await refresh();
      } catch (err) {
        toast.error(err instanceof Error ? err.message : "Error al reconocer alertas");
      } finally {
        setAcknowledging(false);
      }
    },
    [refresh],
  );

  const alerts = useMemo<ClassifiedAlert[]>(
    () =>
      rows.map((alert) => {
        const ageHours = ageInHours(alert, fetchedAtMs);
        return { ...alert, ageHours, severity: severityFor(ageHours) };
      }),
    [rows, fetchedAtMs],
  );

  const bySeverity = useMemo(
    () => ({
      critical: alerts.filter((alert) => alert.severity === "critical"),
      warning: alerts.filter((alert) => alert.severity === "warning"),
      info: alerts.filter((alert) => alert.severity === "info"),
    }),
    [alerts],
  );

  return { alerts, bySeverity, total, loading, error, acknowledging, refresh, acknowledge };
}
