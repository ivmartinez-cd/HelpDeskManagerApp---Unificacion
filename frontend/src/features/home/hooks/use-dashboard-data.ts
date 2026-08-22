"use client";

import { useEffect, useState } from "react";
import { useWatiPendientes } from "@/features/wati/providers/wati-pendientes-provider";
import type { ModuleAccess } from "../config/dashboard-registry";
import { useCalendarioHome } from "./use-calendario-home";
import {
  useClientesPendientesPeriodoAnterior,
  useContadoresResumen,
  useInsumosDashboard,
  useLiquidacionesPendientes,
  useParqueResumen,
  usePendientesResumen,
  useProximosEquipo,
  useSlaHistoria,
  useTurnosHoy,
} from "./use-inicio-data";

/** Cada cuánto se vuelven a pedir todos los datos de Inicio. Es la pantalla
 * que queda abierta todo el día: sin esto, el usuario veía datos del momento
 * del login sin ningún aviso. El dato viejo se mantiene en pantalla mientras
 * llega el nuevo (no vuelve a `loading`). */
export const REFRESH_MS = 5 * 60_000;

/** Todos los datos remotos que consumen las cards y los KPIs, en un solo
 * objeto, para que el orquestador y `CardSlot` no tengan que conocer cada
 * hook. Los fetches siguen siendo los mismos endpoints ya migrados. */
export function useDashboardData(access: ModuleAccess) {
  const [refreshKey, setRefreshKey] = useState(0);
  const [refreshedAt, setRefreshedAt] = useState<Date>(() => new Date());

  useEffect(() => {
    const id = setInterval(() => {
      // Con la pestaña oculta no vale la pena pegarle al backend.
      if (typeof document !== "undefined" && document.visibilityState === "hidden") return;
      setRefreshKey((k) => k + 1);
      setRefreshedAt(new Date());
    }, REFRESH_MS);
    return () => clearInterval(id);
  }, []);

  const turnos = useTurnosHoy(refreshKey);
  const calendario = useCalendarioHome(access.contadores, refreshKey);
  const contadoresResumen = useContadoresResumen(access.contadores, refreshKey);
  const pendientesPeriodo = useClientesPendientesPeriodoAnterior(access.contadores, refreshKey);
  const slaHistoria = useSlaHistoria(access.sla, refreshKey);
  const parque = useParqueResumen(access.cardParque, refreshKey);
  const pendientesResumen = usePendientesResumen(access.sla, refreshKey);
  const insumosDashboard = useInsumosDashboard(access.insumos, refreshKey);
  const liquidacionesPendientes = useLiquidacionesPendientes(access.liquidaciones, refreshKey);
  const proximosEquipo = useProximosEquipo(access.cardEquipo, refreshKey);
  const watiPendientes = useWatiPendientes();

  return {
    refreshedAt,
    turnos,
    calendario,
    contadoresResumen,
    pendientesPeriodo,
    slaHistoria,
    parque,
    pendientesResumen,
    insumosDashboard,
    liquidacionesPendientes,
    proximosEquipo,
    watiPendientes,
  };
}

export type DashboardData = ReturnType<typeof useDashboardData>;
