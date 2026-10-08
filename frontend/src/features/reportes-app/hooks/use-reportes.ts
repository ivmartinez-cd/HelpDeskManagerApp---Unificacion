"use client";

import { useCallback, useEffect, useState } from "react";
import type { Page } from "@/shared/types/pagination";
import {
  reportesAppApi,
  type EstadoReporte,
  type Reporte,
} from "../api/reportes-app-api";

const VACIA: Page<Reporte> = { items: [], total: 0, page: 1, size: 20 };

export function useReportes(
  estado: EstadoReporte | null,
  page: number,
  size: number,
) {
  const [datos, setDatos] = useState<Page<Reporte>>(VACIA);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(
    () =>
      reportesAppApi
        .listar(estado, page, size)
        .then((p) => {
          setDatos(p);
          setError(null);
        })
        .catch((err: unknown) => {
          setError(
            err instanceof Error
              ? err.message
              : "No se pudieron cargar los reportes",
          );
        })
        .finally(() => setLoading(false)),
    [estado, page, size],
  );

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { datos, loading, error, refetch };
}
