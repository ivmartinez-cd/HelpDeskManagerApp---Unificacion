"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { insumosApi } from "../api/insumos-api";
import type { NewDeviceRow } from "../types";

/** Datos de la pantalla Equipos Nuevos: listado + contador de pendientes,
 * refresco automático cada 5 minutos mientras la vista está montada (mismo
 * intervalo que el `usePolling` del legacy para esta pantalla), sync manual
 * contra Insight y toggle de ignorar/restaurar por equipo.
 *
 * No hay librería de polling en el proyecto: es `setInterval` a mano, con la
 * limpieza en el return del efecto. Los refrescos automáticos son "silenciosos"
 * (no tocan el spinner ni tiran toasts): si el backend falla en un ciclo de
 * fondo se conserva la última lista buena y se reintenta a los 5 minutos, en
 * vez de vaciar la tabla que el operario está mirando.
 */

const POLL_INTERVAL_MS = 5 * 60 * 1000;

/** El endpoint pagina, pero esta tabla filtra y ordena del lado del cliente
 * (búsqueda + año + ignorados), así que se pide todo de una. `size` máximo
 * del backend para este listado. */
const PAGE_SIZE = 500;

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

export function useNewDevices() {
  const [rows, setRows] = useState<NewDeviceRow[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [busyDeviceId, setBusyDeviceId] = useState<number | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);

  const mounted = useRef(false);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const refresh = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [page, summary] = await Promise.all([
        insumosApi.listNewDevices({ size: PAGE_SIZE }),
        insumosApi.getNewDevicesSummary(),
      ]);
      if (!mounted.current) return;
      setRows(page.items);
      setPendingCount(summary.pendingCount);
      setLastUpdatedAt(new Date());
      setLoadError(null);
    } catch (err: unknown) {
      if (!mounted.current) return;
      const message = errorMessage(err, "No se pudieron cargar los equipos nuevos.");
      if (silent) {
        // Ciclo de fondo: se deja la última lista buena en pantalla y se
        // registra el motivo en consola para poder diagnosticarlo.
        console.warn("[insumos/equipos-nuevos] falló el refresco automático:", message);
      } else {
        setLoadError(message);
        toast.error(message);
      }
    } finally {
      if (mounted.current && !silent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Carga inicial: `refresh` prende el spinner en forma síncrona a propósito
    // (misma convención que `useCalendarioEvents` de contadores), para no
    // pintar la tabla vacía antes de que llegue la primera respuesta.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void refresh(true);
    }, POLL_INTERVAL_MS);
    return () => window.clearInterval(intervalId);
  }, [refresh]);

  const setDismissed = useCallback(async (device: NewDeviceRow, dismissed: boolean) => {
    setBusyDeviceId(device.deviceId);
    try {
      await insumosApi.setNewDeviceDismissed(device.deviceId, dismissed);
      if (!mounted.current) return;
      setRows((prev) =>
        prev.map((row) => (row.deviceId === device.deviceId ? { ...row, dismissed } : row)),
      );
      setPendingCount((prev) => Math.max(0, prev + (dismissed ? -1 : 1)));
      toast.success(
        dismissed
          ? `${device.serial} marcado como ignorado.`
          : `${device.serial} vuelve a la lista de pendientes.`,
      );
    } catch (err: unknown) {
      toast.error(errorMessage(err, "No se pudo actualizar el equipo."));
    } finally {
      if (mounted.current) setBusyDeviceId(null);
    }
  }, []);

  const sync = useCallback(async () => {
    setSyncing(true);
    try {
      const result = await insumosApi.syncNewDevices();
      toast.success(
        `Sincronización lista: ${result.newDevices} equipo(s) nuevo(s), ${result.pruned} depurado(s).`,
      );
      // El sync devuelve solo el resultado, no el listado: hay que volver a pedirlo.
      await refresh(true);
    } catch (err: unknown) {
      toast.error(errorMessage(err, "No se pudo sincronizar con Insight."));
    } finally {
      if (mounted.current) setSyncing(false);
    }
  }, [refresh]);

  return {
    rows,
    pendingCount,
    loading,
    loadError,
    syncing,
    busyDeviceId,
    lastUpdatedAt,
    refresh,
    setDismissed,
    sync,
  };
}
