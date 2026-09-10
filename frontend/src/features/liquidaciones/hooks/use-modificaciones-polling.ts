"use client";

import { useEffect, useState } from "react";
import { modificacionesApi } from "../api/modificaciones-api";
import type { ModificacionPrestador } from "../types/modificacion";

export interface ModificacionesPollingState {
  noVistas: ModificacionPrestador[];
  total: number;
}

const REFRESH_MS = 60 * 1000;

/** Un solo poller por pestaña de las modificaciones del prestador sin ver
 * (ADR-038) — mismo patrón que `useWatiPendientesPolling`: refresca cada
 * minuto sin volver a mostrar loading. */
export function useModificacionesPolling(enabled: boolean): ModificacionesPollingState {
  const [tick, setTick] = useState(0);
  const [noVistas, setNoVistas] = useState<ModificacionPrestador[]>([]);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    if (!enabled) return;
    let alive = true;
    modificacionesApi
      .listNoVistas(1, 200)
      .then((pagina) => {
        if (!alive) return;
        setNoVistas(pagina.items);
        setTotal(pagina.total);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar modificaciones del prestador:", err);
      });
    return () => {
      alive = false;
    };
  }, [enabled, tick]);

  useEffect(() => {
    if (!enabled) return;
    const id = setInterval(() => setTick((t) => t + 1), REFRESH_MS);
    return () => clearInterval(id);
  }, [enabled]);

  return { noVistas, total };
}
