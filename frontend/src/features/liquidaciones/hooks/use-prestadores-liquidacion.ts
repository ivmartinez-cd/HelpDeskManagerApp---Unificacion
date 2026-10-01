"use client";

import { useCallback, useEffect, useState } from "react";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion } from "../types/liquidaciones";

/** Catálogo completo de prestadores (activos e inactivos) para selects y la
 * pantalla de Prestadores. Sin setLoading(true) sincrónico en el refetch —
 * ver nota en liquidaciones-lista.tsx. */
export function usePrestadoresLiquidacion() {
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    try {
      setPrestadores(await liquidacionesApi.listPrestadores(false));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refetch(); }, [refetch]);

  return { prestadores, loading, refetch };
}
