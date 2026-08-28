"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { insumosApi } from "../api/insumos-api";
import { isLoaded, isSelectable } from "../components/dashboard/request-status";
import type { CustomerSummary, DashboardResponse, RequestRow } from "../types";

/** Datos del Dashboard de Insumos: métricas globales + solicitudes por cliente
 * + expansión + selección por checkbox, todo en UN hook.
 *
 * El legacy repartía esto en `useDashboardMetrics` + `useCustomerRequests` y se
 * pasaban referencias cruzadas entre sí (ver §2.1 de la caracterización, que
 * ya recomendaba colapsarlos al portar: en React pasar "un composable entero"
 * como dependencia de otro no tiene traducción idiomática).
 *
 * Polling: 60s con `setInterval`, pausado cuando la pestaña se oculta y con
 * refresh inmediato al volver (`visibilitychange`). El legacy seguía tickeando
 * oculto porque de ese poll dependían las notificaciones de escritorio — que
 * quedaron FUERA del alcance de esta migración, así que acá sí conviene pausar.
 */

const POLL_INTERVAL_MS = 60_000;

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Error desconocido";
}

export interface DashboardData {
  dashboard: DashboardResponse | null;
  loading: boolean;
  error: string | null;
  lastUpdatedAt: string | null;
  customersWithPending: CustomerSummary[];
  expanded: ReadonlySet<number>;
  requestsByCustomer: Record<number, RequestRow[]>;
  requestsLoading: Record<number, boolean>;
  requestsError: Record<number, string | null>;
  selected: Record<number, ReadonlySet<number>>;
  loadDashboard: (silent?: boolean) => Promise<void>;
  fetchCustomerRequests: (customerId: number) => Promise<void>;
  /** Refresca solicitudes del cliente + métricas globales tras una acción. */
  refreshCustomer: (customerId: number) => Promise<void>;
  toggleExpand: (customerId: number) => void;
  expandCustomer: (customerId: number) => void;
  pendingRequests: (customerId: number) => RequestRow[];
  toggleSelect: (customerId: number, requestId: number) => void;
  toggleSelectAll: (customerId: number) => void;
  deselect: (customerId: number, requestId: number) => void;
  isAllSelected: (customerId: number) => boolean;
}

export function useDashboardData(): DashboardData {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null);

  const [expanded, setExpanded] = useState<ReadonlySet<number>>(() => new Set<number>());
  const [requestsByCustomer, setRequestsByCustomer] = useState<Record<number, RequestRow[]>>({});
  const [requestsLoading, setRequestsLoading] = useState<Record<number, boolean>>({});
  const [requestsError, setRequestsError] = useState<Record<number, string | null>>({});
  const [selected, setSelected] = useState<Record<number, ReadonlySet<number>>>({});

  // Snapshot de pendientes por cliente entre polls: solo se re-piden las
  // solicitudes de los clientes expandidos cuyo contador cambió.
  const prevPending = useRef<Record<number, number>>({});
  const expandedRef = useRef(expanded);
  const requestsRef = useRef(requestsByCustomer);

  useEffect(() => {
    expandedRef.current = expanded;
  }, [expanded]);
  useEffect(() => {
    requestsRef.current = requestsByCustomer;
  }, [requestsByCustomer]);

  const fetchCustomerRequests = useCallback(async (customerId: number) => {
    setRequestsLoading((state) => ({ ...state, [customerId]: true }));
    setRequestsError((state) => ({ ...state, [customerId]: null }));
    try {
      const page = await insumosApi.listRequests({ customerId });
      setRequestsByCustomer((state) => ({ ...state, [customerId]: page.items }));
      setSelected((state) =>
        state[customerId] ? state : { ...state, [customerId]: new Set<number>() },
      );
    } catch (err) {
      setRequestsError((state) => ({ ...state, [customerId]: errorMessage(err) }));
    } finally {
      setRequestsLoading((state) => ({ ...state, [customerId]: false }));
    }
  }, []);

  const loadDashboard = useCallback(
    async (silent = false) => {
      if (!silent) setLoading(true);
      try {
        const data = await insumosApi.getDashboard();
        setDashboard(data);
        setError(null);
        setLastUpdatedAt(new Date().toISOString());

        const before = prevPending.current;
        const stale = data.perCustomer.filter(
          (customer) =>
            expandedRef.current.has(customer.customerId) &&
            requestsRef.current[customer.customerId] !== undefined &&
            (before[customer.customerId] ?? 0) !== customer.pending,
        );
        prevPending.current = Object.fromEntries(
          data.perCustomer.map((customer) => [customer.customerId, customer.pending]),
        );
        await Promise.all(stale.map((customer) => fetchCustomerRequests(customer.customerId)));
      } catch (err) {
        setError(errorMessage(err));
      } finally {
        if (!silent) setLoading(false);
      }
    },
    [fetchCustomerRequests],
  );

  const refreshCustomer = useCallback(
    async (customerId: number) => {
      await fetchCustomerRequests(customerId);
      await loadDashboard(true);
    },
    [fetchCustomerRequests, loadDashboard],
  );

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    let handle: ReturnType<typeof setInterval> | null = null;
    const start = () => {
      if (handle === null) handle = setInterval(() => void loadDashboard(true), POLL_INTERVAL_MS);
    };
    const stop = () => {
      if (handle !== null) {
        clearInterval(handle);
        handle = null;
      }
    };
    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        void loadDashboard(true);
        start();
      } else {
        stop();
      }
    };
    if (document.visibilityState === "visible") start();
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      stop();
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [loadDashboard]);

  const expandCustomer = useCallback(
    (customerId: number) => {
      if (expandedRef.current.has(customerId)) return;
      setExpanded((state) => new Set(state).add(customerId));
      if (requestsRef.current[customerId] === undefined) void fetchCustomerRequests(customerId);
    },
    [fetchCustomerRequests],
  );

  const toggleExpand = useCallback(
    (customerId: number) => {
      if (expandedRef.current.has(customerId)) {
        setExpanded((state) => {
          const next = new Set(state);
          next.delete(customerId);
          return next;
        });
        return;
      }
      expandCustomer(customerId);
    },
    [expandCustomer],
  );

  // Filas a mostrar en la tabla: todo lo que no sea un pedido propio ya
  // confirmado. Un pedido activo sin confirmar entrega (hasActiveSupply)
  // sigue en esta lista con su badge de aviso — ver isLoaded en
  // request-status.ts, feature "pedido activo sin confirmar entrega".
  const pendingRequests = useCallback(
    (customerId: number) => (requestsByCustomer[customerId] ?? []).filter((row) => !isLoaded(row)),
    [requestsByCustomer],
  );

  const toggleSelect = useCallback((customerId: number, requestId: number) => {
    setSelected((state) => {
      const next = new Set(state[customerId] ?? []);
      if (next.has(requestId)) next.delete(requestId);
      else next.add(requestId);
      return { ...state, [customerId]: next };
    });
  }, []);

  const deselect = useCallback((customerId: number, requestId: number) => {
    setSelected((state) => {
      const current = state[customerId];
      if (!current?.has(requestId)) return state;
      const next = new Set(current);
      next.delete(requestId);
      return { ...state, [customerId]: next };
    });
  }, []);

  const isAllSelected = useCallback(
    (customerId: number) => {
      const pending = (requestsByCustomer[customerId] ?? []).filter((row) => isSelectable(row));
      if (pending.length === 0) return false;
      const current = selected[customerId];
      if (!current) return false;
      return pending.every((row) => current.has(row.requestId));
    },
    [requestsByCustomer, selected],
  );

  const toggleSelectAll = useCallback(
    (customerId: number) => {
      const pending = (requestsByCustomer[customerId] ?? []).filter((row) => isSelectable(row));
      if (pending.length === 0) return;
      const allSelected = isAllSelected(customerId);
      setSelected((state) => {
        const next = new Set(state[customerId] ?? []);
        for (const row of pending) {
          if (allSelected) next.delete(row.requestId);
          else next.add(row.requestId);
        }
        return { ...state, [customerId]: next };
      });
    },
    [requestsByCustomer, isAllSelected],
  );

  const customersWithPending = useMemo(
    () => (dashboard?.perCustomer ?? []).filter((customer) => customer.pending > 0),
    [dashboard],
  );

  return {
    dashboard,
    loading,
    error,
    lastUpdatedAt,
    customersWithPending,
    expanded,
    requestsByCustomer,
    requestsLoading,
    requestsError,
    selected,
    loadDashboard,
    fetchCustomerRequests,
    refreshCustomer,
    toggleExpand,
    expandCustomer,
    pendingRequests,
    toggleSelect,
    toggleSelectAll,
    deselect,
    isAllSelected,
  };
}
