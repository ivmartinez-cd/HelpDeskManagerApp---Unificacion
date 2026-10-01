"use client";

import { useEffect, useState } from "react";
import { pendientesApi } from "../api/pendientes-api";
import type { IncidenteSinCerrar } from "../types/pendientes";
import { prestadoresApi } from "@/features/prestadores/api/prestadores-api";
import type { OperadorOption } from "@/features/prestadores/types/prestadores";
import { useSession } from "@/services/session-provider";
import type { StatsColumn } from "@/shared/components/ui/stats-table";
import { statsSortField, useStatsServerSort } from "@/shared/components/ui/stats-table-sort";

export const MIS_PST = "__mis_pst__";
export const TODOS = "__todos__";
export const PENDIENTES_PAGE_SIZE = 100;

export function scopeToOperadorId(scope: string): string | undefined {
  return scope === TODOS ? undefined : scope === MIS_PST ? undefined : scope;
}

/** Pendientes a cerrar paginados y ordenados en el servidor, filtrados por
 * scope (mis PST / todos / un operador). `setResultado` y `setError` quedan
 * para el "Actualizar" del componente. */
export function usePendientesACerrar(columns: StatsColumn<IncidenteSinCerrar>[]) {
  const { user, can } = useSession();
  const canVerOperadores = user.isSuperadmin || can("prestadores", "view");

  const [scope, setScope] = useState<string>(MIS_PST);
  const [operadores, setOperadores] = useState<OperadorOption[]>([]);
  const [incidentes, setIncidentes] = useState<IncidenteSinCerrar[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  // Pagina en el servidor: el backend ordena todos los pendientes.
  const { sort, onToggleSort } = useStatsServerSort(columns, () => setPage(1));
  const sortBy = statsSortField(columns, sort.key);
  const sortDir = sort.direction;

  const [prevScope, setPrevScope] = useState(scope);
  if (scope !== prevScope) {
    setPrevScope(scope);
    setLoading(true);
    setError(null);
    setIncidentes([]);
    setPage(1);
  }

  useEffect(() => {
    if (!canVerOperadores) return;
    prestadoresApi.listOperadores().then(setOperadores).catch(() => setOperadores([]));
  }, [canVerOperadores]);

  useEffect(() => {
    let active = true;
    const operadorId = scopeToOperadorId(scope);
    pendientesApi
      .listPendientes({ operadorId, page, size: PENDIENTES_PAGE_SIZE, sortBy, sortDir })
      .then((res) => {
        if (!active) return;
        setIncidentes(res.items);
        setTotal(res.total);
      })
      .catch((err: unknown) => {
        if (!active) return;
        console.error("Error al cargar pendientes a cerrar:", err);
        setError(
          err instanceof Error ? err.message : "No se pudieron cargar los pendientes a cerrar.",
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [scope, page, sortBy, sortDir]);

  const setResultado = (res: { items: IncidenteSinCerrar[]; total: number }) => {
    setIncidentes(res.items);
    setTotal(res.total);
  };

  return {
    canVerOperadores, scope, setScope, operadores, incidentes, total, page, setPage,
    sort, onToggleSort, sortBy, sortDir, loading, error, setError, setResultado,
  };
}
