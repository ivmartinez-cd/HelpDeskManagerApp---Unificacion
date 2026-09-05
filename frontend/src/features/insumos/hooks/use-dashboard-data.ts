"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { insumosApi } from "../api/insumos-api";
import { isLoaded } from "../components/dashboard/request-status";
import type { CustomerSummary, DashboardResponse, RequestRow } from "../types";
import { useRequestSelection } from "./use-request-selection";

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
  const {
    selected,
    ensureCustomerSelection,
    toggleSelect,
    toggleSelectAll,
    deselect,
    isAllSelected,
  } = useRequestSelection(requestsByCustomer);

  // Snapshot de pendientes por cliente entre polls: para clientes colapsados,
  // invalidar el cache viejo cuando el contador cambió (sin pedirlo por HTTP).
  const prevPending = useRef<Record<number, number>>({});
  // Divergencias contador/filas para las que ya se pidió un refetch, como
  // "pendientes:filas". Si el refetch no la resuelve (los dos endpoints
  // clasifican distinto una fila, no es una foto vieja), evita reintentar en
  // cada poll para siempre.
  const resyncAttempts = useRef<Record<number, string>>({});
  // Un fetch en vuelo por cliente: poll de 60s, tick por visibilitychange,
  // refresh post-carga y expandCustomer pueden pisarse — sin cancelar el
  // anterior, la respuesta que salió primero puede resolver última.
  const inFlight = useRef<Map<number, AbortController>>(new Map());
  const expandedRef = useRef(expanded);
  const requestsRef = useRef(requestsByCustomer);

  useEffect(() => {
    expandedRef.current = expanded;
  }, [expanded]);
  useEffect(() => {
    requestsRef.current = requestsByCustomer;
  }, [requestsByCustomer]);

  const fetchCustomerRequests = useCallback(
    async (customerId: number) => {
      inFlight.current.get(customerId)?.abort();
      const controller = new AbortController();
      inFlight.current.set(customerId, controller);

      setRequestsLoading((state) => ({ ...state, [customerId]: true }));
      setRequestsError((state) => ({ ...state, [customerId]: null }));
      try {
        const page = await insumosApi.listRequests({ customerId }, { signal: controller.signal });
        setRequestsByCustomer((state) => ({ ...state, [customerId]: page.items }));
        ensureCustomerSelection(customerId);
      } catch (err) {
        // Abortado porque arrancó un fetch más nuevo para este cliente: no es
        // un error a mostrar, y el estado (loading/errors) ya le pertenece a
        // ese otro.
        if (err instanceof DOMException && err.name === "AbortError") return;
        setRequestsError((state) => ({ ...state, [customerId]: errorMessage(err) }));
      } finally {
        if (inFlight.current.get(customerId) === controller) {
          inFlight.current.delete(customerId);
          setRequestsLoading((state) => ({ ...state, [customerId]: false }));
        }
      }
    },
    [ensureCustomerSelection],
  );

  const loadDashboard = useCallback(
    async (silent = false) => {
      if (!silent) setLoading(true);
      try {
        const data = await insumosApi.getDashboard();
        setDashboard(data);
        setError(null);
        setLastUpdatedAt(new Date().toISOString());

        // Resincronizar el panel expandido con el contador de la fila. El
        // criterio es la cantidad de filas que la tabla REALMENTE muestra
        // (post-isLoaded), no un snapshot aparte: si un refetch anterior no
        // corrió, falló o llegó fuera de orden, el próximo poll lo repara solo.
        const before = prevPending.current;
        const stale: number[] = [];
        for (const customer of data.perCustomer) {
          const cid = customer.customerId;
          const cached = requestsRef.current[cid];
          if (cached === undefined) continue; // nunca se expandió: expandCustomer las trae

          if (!expandedRef.current.has(cid)) {
            // Colapsado: invalidar el cache en vez de pedir por HTTP algo que
            // nadie mira. Sin esto, toggleExpand vuelve a servir filas viejas
            // (solo fetchea si no hay cache).
            if ((before[cid] ?? 0) !== customer.pending) {
              setRequestsByCustomer((state) => {
                const next = { ...state };
                delete next[cid];
                return next;
              });
            }
            continue;
          }

          const shown = cached.filter((row) => !isLoaded(row)).length;
          if (shown === customer.pending) {
            delete resyncAttempts.current[cid];
            continue;
          }
          const divergence = `${customer.pending}:${shown}`;
          if (resyncAttempts.current[cid] === divergence) continue;
          resyncAttempts.current[cid] = divergence;
          stale.push(cid);
        }
        prevPending.current = Object.fromEntries(
          data.perCustomer.map((customer) => [customer.customerId, customer.pending]),
        );
        await Promise.all(stale.map((customerId) => fetchCustomerRequests(customerId)));
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
