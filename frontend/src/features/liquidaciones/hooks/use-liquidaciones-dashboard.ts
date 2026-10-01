"use client";

import { useCallback, useEffect, useState } from "react";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  FacturadoPorPeriodoItem,
  Liquidacion,
  PrestadorLiquidacion,
  RankingPrestador,
} from "../types/liquidaciones";

/** Datos del dashboard. Sin setLoading(true) sincrónico — ver nota en
 * liquidaciones-lista.tsx. listAll() usa fetchCatalogoCompleto para evitar el
 * truncamiento silencioso. `prestadores` solo alimenta el select del modal de
 * importación — el ranking/gráfico ya vienen agregados por nombre desde el
 * backend. */
export function useLiquidacionesDashboard() {
  const [liquidaciones, setLiquidaciones] = useState<Liquidacion[]>([]);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [facturadoPorPeriodo, setFacturadoPorPeriodo] = useState<FacturadoPorPeriodoItem[]>([]);
  const [ranking, setRanking] = useState<RankingPrestador[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    try {
      const [liqs, prest, facturado, top] = await Promise.all([
        liquidacionesApi.listAll(),
        liquidacionesApi.listPrestadores(),
        liquidacionesApi.getFacturadoPorPeriodo(),
        liquidacionesApi.getRankingPrestadores(),
      ]);
      setLiquidaciones(liqs);
      setPrestadores(prest);
      setFacturadoPorPeriodo(facturado);
      setRanking(top);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { liquidaciones, prestadores, facturadoPorPeriodo, ranking, loading, refetch };
}
