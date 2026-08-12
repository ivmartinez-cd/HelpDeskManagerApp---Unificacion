"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { insumosApi } from "../api/insumos-api";
import type { CustomerRow } from "../types";

/** Estado de la pantalla Clientes: lista completa + toggle individual + bulk
 * toggle + sync desde Insight. Sin polling automático (la lista de clientes
 * cambia raramente; el operario sincroniza a demanda o al abrir la pantalla). */

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

export function useCustomers() {
  const [rows, setRows] = useState<CustomerRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [bulkLoading, setBulkLoading] = useState(false);

  const mounted = useRef(false);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await insumosApi.listCustomers();
      if (!mounted.current) return;
      setRows(data);
      setLoadError(null);
    } catch (err: unknown) {
      if (!mounted.current) return;
      const msg = errorMessage(err, "No se pudieron cargar los clientes.");
      setLoadError(msg);
      toast.error(msg);
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  const toggle = useCallback(async (row: CustomerRow, enabled: boolean) => {
    setBusyId(row.customer_id);
    try {
      await insumosApi.toggleCustomer(row.customer_id, enabled);
      if (!mounted.current) return;
      setRows((prev) =>
        prev.map((r) => (r.customer_id === row.customer_id ? { ...r, enabled } : r)),
      );
      toast.success(`${row.name} ${enabled ? "habilitado" : "deshabilitado"}.`);
    } catch (err: unknown) {
      toast.error(errorMessage(err, "No se pudo actualizar el cliente."));
    } finally {
      if (mounted.current) setBusyId(null);
    }
  }, []);

  const bulkToggle = useCallback(async (enabled: boolean) => {
    setBulkLoading(true);
    try {
      await insumosApi.bulkToggleCustomers(enabled);
      if (!mounted.current) return;
      setRows((prev) => prev.map((r) => ({ ...r, enabled })));
      toast.success(
        enabled ? "Todos los clientes habilitados." : "Todos los clientes deshabilitados.",
      );
    } catch (err: unknown) {
      toast.error(errorMessage(err, "No se pudo actualizar los clientes."));
    } finally {
      if (mounted.current) setBulkLoading(false);
    }
  }, []);

  const sync = useCallback(async () => {
    setSyncing(true);
    try {
      const result = await insumosApi.syncCustomers();
      if (!mounted.current) return;
      toast.success(`Sincronización lista: ${result.count} cliente(s) en Insight.`);
      await refresh();
    } catch (err: unknown) {
      toast.error(errorMessage(err, "No se pudo sincronizar clientes desde Insight."));
    } finally {
      if (mounted.current) setSyncing(false);
    }
  }, [refresh]);

  const markHasContacts = useCallback((customerId: number, hasContacts: boolean) => {
    setRows((prev) =>
      prev.map((r) => (r.customer_id === customerId ? { ...r, has_contacts: hasContacts } : r)),
    );
  }, []);

  return {
    rows,
    loading,
    loadError,
    busyId,
    syncing,
    bulkLoading,
    toggle,
    bulkToggle,
    sync,
    markHasContacts,
  };
}
