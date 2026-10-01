"use client";

import { useCallback, useEffect, useState } from "react";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { Liquidacion, PrestadorLiquidacion } from "../types/liquidaciones";

export const PAGE_SIZE = 50;

interface FiltrosLista {
  prestador: string;
  estado: string;
  periodo: string;
  anio: string;
}

/** Página de liquidaciones con filtros + catálogos de los selects (prestadores
 * y períodos). Cambiar un filtro vuelve a pedir la página 1; `refetch(p)` pide
 * una página puntual. Sin setLoading(true) sincrónico — ver nota en
 * liquidaciones-dashboard.tsx. */
export function useLiquidacionesLista({ prestador, estado, periodo, anio }: FiltrosLista) {
  const [liquidaciones, setLiquidaciones] = useState<Liquidacion[]>([]);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [periodos, setPeriodos] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  const refetch = useCallback(
    async (p: number) => {
      try {
        const res = await liquidacionesApi.list({
          prestadorId: prestador || undefined,
          estado: estado || undefined,
          periodo: periodo || undefined,
          anio: anio ? Number(anio) : undefined,
          page: p,
          size: PAGE_SIZE,
        });
        setLiquidaciones(res.items);
        setTotal(res.total);
      } finally {
        setLoading(false);
      }
    },
    [prestador, estado, periodo, anio],
  );

  useEffect(() => {
    void Promise.all([
      liquidacionesApi.listPrestadores().then(setPrestadores),
      liquidacionesApi.listPeriodos().then(setPeriodos),
    ]);
  }, []);

  useEffect(() => {
    void refetch(1);
  }, [refetch]);

  return { liquidaciones, prestadores, periodos, loading, total, refetch };
}
