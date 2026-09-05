"use client";

import { useCallback, useState } from "react";
import { isSelectable } from "../components/dashboard/request-status";
import type { RequestRow } from "../types";

/** Selección por checkbox de solicitudes por cliente — extraído de
 * `use-dashboard-data.ts` (§4, límite de archivo) porque es un colaborador
 * autocontenido: solo necesita las filas ya cargadas por cliente, no el resto
 * del estado del dashboard. */
export interface RequestSelection {
  selected: Record<number, ReadonlySet<number>>;
  ensureCustomerSelection: (customerId: number) => void;
  toggleSelect: (customerId: number, requestId: number) => void;
  toggleSelectAll: (customerId: number) => void;
  deselect: (customerId: number, requestId: number) => void;
  isAllSelected: (customerId: number) => boolean;
}

export function useRequestSelection(
  requestsByCustomer: Record<number, RequestRow[]>,
): RequestSelection {
  const [selected, setSelected] = useState<Record<number, ReadonlySet<number>>>({});

  const ensureCustomerSelection = useCallback((customerId: number) => {
    setSelected((state) =>
      state[customerId] ? state : { ...state, [customerId]: new Set<number>() },
    );
  }, []);

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

  return { selected, ensureCustomerSelection, toggleSelect, toggleSelectAll, deselect, isAllSelected };
}
