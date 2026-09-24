"use client";

import { useEffect, useState } from "react";
import { despachadosApi } from "../api/despachados-api";

/** Pills del item "Despachados" del submenú de Insumos: alertas rojas y
 * naranjas abiertas (`/despachados/resumen`). Fetch aislado de
 * `useInsumosNavCounts` a propósito: si Despachados falla (o el usuario no
 * tiene datos todavía), los contadores de Solicitudes/Offline siguen andando. */

const POLL_INTERVAL_MS = 60_000;

export interface DespachadosNavCounts {
  rojas: number;
  naranjas: number;
}

const EMPTY: DespachadosNavCounts = { rojas: 0, naranjas: 0 };

export function useDespachadosNavCounts(): DespachadosNavCounts {
  const [counts, setCounts] = useState<DespachadosNavCounts>(EMPTY);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const resumen = await despachadosApi.getResumen();
        if (!cancelled) {
          setCounts({ rojas: resumen.alertasRojas, naranjas: resumen.alertasNaranjas });
        }
      } catch (err: unknown) {
        // Badge informativo: si falla se deja en 0 sin romper la navegación.
        if (!cancelled) {
          console.warn("[insumos] no se pudieron cargar los contadores de Despachados:", err);
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
