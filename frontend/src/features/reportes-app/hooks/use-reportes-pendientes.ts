"use client";

import { useEffect, useState } from "react";
import { reportesAppApi } from "../api/reportes-app-api";

/** Reportes que esperan algo del superadmin: `propuesto` (falta su OK) y
 * `resuelto` (falta Integrar). Reemplaza los avisos de la campanita: marca el
 * ícono del pie del menú lateral. Solo pide el total (size=1). */

const POLL_INTERVAL_MS = 90_000;

export interface ReportesPendientes {
  propuestos: number;
  resueltos: number;
}

const VACIO: ReportesPendientes = { propuestos: 0, resueltos: 0 };

export function useReportesPendientes(): ReportesPendientes {
  const [pendientes, setPendientes] = useState<ReportesPendientes>(VACIO);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const [propuestos, resueltos] = await Promise.all([
          reportesAppApi.listar("propuesto", 1, 1),
          reportesAppApi.listar("resuelto", 1, 1),
        ]);
        if (!cancelled) {
          setPendientes({ propuestos: propuestos.total, resueltos: resueltos.total });
        }
      } catch (err: unknown) {
        // Indicador informativo: si falla queda sin marcar, sin romper el menú.
        if (!cancelled) {
          console.warn("[reportes-app] no se pudieron contar los pendientes:", err);
          setPendientes(VACIO);
        }
      }
    };
    const alVolver = () => {
      if (document.visibilityState === "visible") void load();
    };

    void load();
    const interval = setInterval(load, POLL_INTERVAL_MS);
    document.addEventListener("visibilitychange", alVolver);
    return () => {
      cancelled = true;
      clearInterval(interval);
      document.removeEventListener("visibilitychange", alVolver);
    };
  }, []);

  return pendientes;
}
