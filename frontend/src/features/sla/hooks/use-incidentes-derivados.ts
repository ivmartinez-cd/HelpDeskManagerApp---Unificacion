"use client";

import { useEffect, useState } from "react";
import { derivadosApi } from "../api/derivados-api";
import type { IncidenteDerivado } from "../types/derivados";
import { prestadoresApi } from "@/features/prestadores/api/prestadores-api";
import type { OperadorOption } from "@/features/prestadores/types/prestadores";
import { useSession } from "@/services/session-provider";

export const MIS_PST = "__mis_pst__";
export const TODOS = "__todos__";

function currentMonthValue(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

function monthValueToPeriodo(value: string): string {
  return value.replace("-", "");
}

function scopeToOperadorId(scope: string): string | undefined {
  return scope === MIS_PST || scope === TODOS ? undefined : scope;
}

export function useIncidentesDerivados() {
  const { user, can } = useSession();
  const canVerOperadores = user.isSuperadmin || can("prestadores", "view");

  const [monthValue, setMonthValue] = useState<string>(currentMonthValue());
  const [scope, setScope] = useState<string>(MIS_PST);
  const [operadores, setOperadores] = useState<OperadorOption[]>([]);
  const [incidentes, setIncidentes] = useState<IncidenteDerivado[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [prevKey, setPrevKey] = useState(`${monthValue}|${scope}`);
  const currentKey = `${monthValue}|${scope}`;
  if (currentKey !== prevKey) {
    setPrevKey(currentKey);
    setLoading(true);
    setError(null);
    setIncidentes([]);
  }

  useEffect(() => {
    if (!canVerOperadores) return;
    prestadoresApi.listOperadores().then(setOperadores).catch(() => setOperadores([]));
  }, [canVerOperadores]);

  useEffect(() => {
    let active = true;
    const periodo = monthValueToPeriodo(monthValue);
    derivadosApi
      .listIncidentes(periodo, { operadorId: scopeToOperadorId(scope) })
      .then((items) => {
        if (!active) return;
        setIncidentes(items);
      })
      .catch((err: unknown) => {
        if (!active) return;
        console.error("Error al cargar incidentes derivados:", err);
        setError(
          err instanceof Error ? err.message : "No se pudieron cargar los incidentes derivados.",
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [monthValue, scope]);

  return {
    canVerOperadores,
    monthValue,
    setMonthValue,
    scope,
    setScope,
    operadores,
    incidentes,
    loading,
    error,
    isSuperadmin: user.isSuperadmin,
  };
}
