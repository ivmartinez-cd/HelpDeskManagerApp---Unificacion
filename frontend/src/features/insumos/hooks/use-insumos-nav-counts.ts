"use client";

import { useEffect, useState } from "react";
import { insumosApi } from "../api/insumos-api";

/** Contadores de los badges del submenú de Insumos (Solicitudes/Equipos
 * offline). Pide solo lo mínimo de cada endpoint — `totals` del dashboard y
 * `candidateCount` de `/offline-devices/summary` (mismo endpoint que consulta
 * `TheSidebar` cada 5 min en el legacy, ver SDSINSUMOS_CARACTERIZACION_FRONTEND.md)
 * — para no duplicar el fetch pesado de `useDashboardData`/`useOfflineDevices`,
 * que traen mucho más de lo que necesita un badge del sidebar. */

const POLL_INTERVAL_MS = 60_000;

export interface InsumosNavCounts {
  pending: number;
  critical: number;
  offline: number;
}

const EMPTY: InsumosNavCounts = { pending: 0, critical: 0, offline: 0 };

export function useInsumosNavCounts(): InsumosNavCounts {
  const [counts, setCounts] = useState<InsumosNavCounts>(EMPTY);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const [dashboard, offlineSummary] = await Promise.all([
          insumosApi.getDashboard(),
          insumosApi.getOfflineSummary(),
        ]);
        if (cancelled) return;
        setCounts({
          pending: dashboard.totals.pending ?? 0,
          critical: dashboard.totals.critical ?? 0,
          offline: offlineSummary.candidateCount,
        });
      } catch (err: unknown) {
        // Los badges del sidebar son un extra informativo: si falla el fetch
        // no tiene sentido romper la navegación, se dejan en 0.
        if (!cancelled) {
          console.warn("[insumos] no se pudieron cargar los contadores del sidebar:", err);
          setCounts(EMPTY);
        }
      }
    };

    void load();
    const interval = setInterval(load, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return counts;
}
