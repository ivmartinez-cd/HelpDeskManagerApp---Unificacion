"use client";

import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { CotizacionUsd } from "../types/liquidaciones";
import { formatARS, formatUSD } from "../lib/format";

export type Moneda = "ARS" | "USD";

interface MonedaCtx {
  moneda: Moneda;
  setMoneda: (m: Moneda) => void;
  /** `null` cuando la liquidación no tiene cotización (período < 2026-01 o
   * todavía sin sincronizar) — el switch del header queda deshabilitado y
   * `formatMonto` ignora `moneda` y siempre devuelve ARS. */
  cotizacion: CotizacionUsd | null;
  formatMonto: (n: number | null) => string;
}

const MonedaContext = createContext<MonedaCtx | null>(null);

export function MonedaProvider({
  cotizacion,
  children,
}: {
  cotizacion: CotizacionUsd | null;
  children: ReactNode;
}) {
  const [moneda, setMoneda] = useState<Moneda>("ARS");

  const value = useMemo<MonedaCtx>(() => {
    const formatMonto = (n: number | null) => {
      if (n === null) return "—";
      if (moneda === "ARS" || !cotizacion) return formatARS(n);
      return formatUSD(n / cotizacion.venta);
    };
    return { moneda, setMoneda, cotizacion, formatMonto };
  }, [moneda, cotizacion]);

  return <MonedaContext.Provider value={value}>{children}</MonedaContext.Provider>;
}

export function useMoneda(): MonedaCtx {
  const ctx = useContext(MonedaContext);
  if (!ctx) throw new Error("useMoneda() requiere MonedaProvider");
  return ctx;
}
