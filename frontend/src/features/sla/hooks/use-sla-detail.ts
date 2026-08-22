"use client";

import { useEffect, useState } from "react";
import { slaApi, type FiltroOperador } from "../api/sla-api";
import type { IncidenteVencido, SlaResumen } from "../types/sla";
import { prestadoresApi } from "@/features/prestadores/api/prestadores-api";
import type { OperadorOption } from "@/features/prestadores/types/prestadores";
import { useSession } from "@/services/session-provider";

export const MIS_PST = "__mis_pst__";
export const TODOS = "__todos__";

function scopeToFiltro(scope: string): FiltroOperador | undefined {
  if (scope === MIS_PST) return undefined;
  if (scope === TODOS) return { todos: true };
  return { operadorId: scope };
}

export function formatUpdatedAt(iso: string): string {
  const date = new Date(iso);
  return `${date.toLocaleDateString("es-AR")} ${date.toLocaleTimeString("es-AR", {
    hour: "2-digit",
    minute: "2-digit",
  })}`;
}

function currentMonthValue(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

function monthValueToPeriodo(value: string): string {
  return value.replace("-", "");
}

export function useSlaDetail() {
  const { user, can } = useSession();
  const canUpdate = user.isSuperadmin || can("sla", "update");
  const canVerOperadores = user.isSuperadmin || can("prestadores", "view");

  const [monthValue, setMonthValue] = useState<string>(currentMonthValue());
  const [scope, setScope] = useState<string>(MIS_PST);
  const [operadores, setOperadores] = useState<OperadorOption[]>([]);
  const [resumen, setResumen] = useState<SlaResumen | null>(null);
  const [incidentes, setIncidentes] = useState<IncidenteVencido[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Resetear datos al cambiar de período o de operador — "ajustar estado
  // durante el render" en vez de dentro del efecto (mismo patrón que
  // confirmation-modal.tsx).
  const [prevKey, setPrevKey] = useState(`${monthValue}|${scope}`);
  const currentKey = `${monthValue}|${scope}`;
  if (currentKey !== prevKey) {
    setPrevKey(currentKey);
    setLoading(true);
    setError(null);
    setResumen(null);
    setIncidentes([]);
  }

  useEffect(() => {
    if (!canVerOperadores) return;
    prestadoresApi.listOperadores().then(setOperadores).catch(() => setOperadores([]));
  }, [canVerOperadores]);

  useEffect(() => {
    let active = true;
    const periodo = monthValueToPeriodo(monthValue);
    const filtro = scopeToFiltro(scope);
    Promise.all([slaApi.getResumen(periodo), slaApi.listIncidentesVencidos(periodo, filtro)])
      .then(([res, inc]) => {
        if (!active) return;
        setResumen(res);
        setIncidentes(inc);
      })
      .catch((err: unknown) => {
        if (!active) return;
        console.error("Error al cargar datos SLA:", err);
        setError(err instanceof Error ? err.message : "No se pudieron cargar los datos SLA.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [monthValue, scope]);

  const handleRefresh = () => {
    const periodo = monthValueToPeriodo(monthValue);
    const filtro = scopeToFiltro(scope);
    setRefreshing(true);
    setError(null);
    slaApi
      .refreshResumen(periodo)
      .then(() =>
        Promise.all([slaApi.getResumen(periodo), slaApi.listIncidentesVencidos(periodo, filtro)]),
      )
      .then(([res, inc]) => {
        setResumen(res);
        setIncidentes(inc);
      })
      .catch((err: unknown) => {
        console.error("Error al actualizar el SLA:", err);
        setError(err instanceof Error ? err.message : "No se pudo actualizar el SLA.");
      })
      .finally(() => setRefreshing(false));
  };

  return {
    canUpdate,
    canVerOperadores,
    monthValue,
    setMonthValue,
    scope,
    setScope,
    operadores,
    resumen,
    incidentes,
    loading,
    refreshing,
    error,
    handleRefresh,
  };
}
