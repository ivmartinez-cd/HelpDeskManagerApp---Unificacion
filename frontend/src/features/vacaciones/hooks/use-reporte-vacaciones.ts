"use client";

import { useCallback, useEffect, useState } from "react";
import { reportesApi } from "../api/reportes-api";
import type { ReporteVacaciones } from "../types/vacaciones";

/** Reporte de vacaciones del ciclo. `setError` queda expuesto porque la
 * pantalla muestra en el mismo banner los errores de exportación. */
export function useReporteVacaciones() {
  const [data, setData] = useState<ReporteVacaciones | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    reportesApi
      .getReporte()
      .then((r) => {
        setData(r);
        setError(null);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar el reporte:", err);
        setError("No se pudo cargar el reporte de vacaciones.");
      });
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, error, setError, refetch };
}
