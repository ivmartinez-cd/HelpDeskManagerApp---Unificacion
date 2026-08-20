"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { insumosApi } from "../api/insumos-api";
import type {
  DeleteOfflinePayload,
  MassOutageRow,
  OfflineDeviceRow,
  VerifyOfflinePayload,
  VerifyOfflineResponse,
} from "../types";

/** Datos de la pantalla Equipos Offline: listado + outages, refresco automático
 * cada 5 minutos (mismo intervalo que el legacy para esta pantalla), verificación
 * manual contra CD (SOAP) y baja en el PortalWeb de SDS.
 *
 * El toggle de dismissed actualiza el estado local de forma optimista: la fila
 * sigue visible (opacidad reducida), igual que Equipos Nuevos. La verificación
 * y la baja masiva hacen un refresh completo al terminar porque cambian los
 * veredictos y los contadores. */

const POLL_INTERVAL_MS = 5 * 60 * 1000;
const PAGE_SIZE = 500;

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

export function useOfflineDevices() {
  const [rows, setRows] = useState<OfflineDeviceRow[]>([]);
  const [outages, setOutages] = useState<MassOutageRow[]>([]);
  const [candidateCount, setCandidateCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);

  const [verifying, setVerifying] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [busyDeviceId, setBusyDeviceId] = useState<number | null>(null);

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
      const [devicesPage, outagesPage, summary] = await Promise.all([
        insumosApi.listOfflineDevices({ size: PAGE_SIZE }),
        insumosApi.listOfflineOutages({ size: PAGE_SIZE }),
        insumosApi.getOfflineSummary(),
      ]);
      if (!mounted.current) return;
      setRows(devicesPage.items);
      setOutages(outagesPage.items);
      setCandidateCount(summary.candidateCount);
      setLastUpdatedAt(new Date());
      setLoadError(null);
    } catch (err: unknown) {
      if (!mounted.current) return;
      const message = errorMessage(err, "No se pudieron cargar los equipos offline.");
      if (silent) {
        console.warn("[insumos/equipos-offline] falló el refresco automático:", message);
      } else {
        setLoadError(message);
        toast.error(message);
      }
    } finally {
      if (mounted.current && !silent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void refresh(true);
    }, POLL_INTERVAL_MS);
    return () => window.clearInterval(intervalId);
  }, [refresh]);

  const setDismissed = useCallback(async (device: OfflineDeviceRow, dismissed: boolean) => {
    setBusyDeviceId(device.deviceId);
    try {
      await insumosApi.setOfflineDismissed(device.deviceId, dismissed);
      if (!mounted.current) return;
      setRows((prev) =>
        prev.map((row) =>
          row.deviceId === device.deviceId ? { ...row, offlineDismissed: dismissed } : row,
        ),
      );
      toast.success(
        dismissed
          ? `${device.serial} marcado como descartado.`
          : `${device.serial} vuelve a la vista offline.`,
      );
    } catch (err: unknown) {
      toast.error(errorMessage(err, "No se pudo actualizar el equipo."));
    } finally {
      if (mounted.current) setBusyDeviceId(null);
    }
  }, []);

  const verify = useCallback(
    async (payload: VerifyOfflinePayload): Promise<VerifyOfflineResponse | null> => {
      setVerifying(true);
      try {
        const result = await insumosApi.verifyOfflineDevices(payload);
        toast.success(
          `Verificación lista: ${result.checked} equipo(s) consultado(s) ` +
            `— Bodega: ${result.bodega}, En cliente: ${result.enCliente}, ` +
            `Otro cliente: ${result.otroCliente}, Errores: ${result.errores}. ` +
            (result.remaining > 0 ? `Quedan ${result.remaining} sin verificar.` : ""),
        );
        await refresh(true);
        return result;
      } catch (err: unknown) {
        const message = errorMessage(err, "Error al verificar equipos contra Canal Directo.");
        toast.error(message);
        return null;
      } finally {
        if (mounted.current) setVerifying(false);
      }
    },
    [refresh],
  );

  const deleteDevices = useCallback(
    async (payload: DeleteOfflinePayload): Promise<boolean> => {
      setDeleting(true);
      try {
        const result = await insumosApi.deleteOfflineDevices(payload);
        const failed = result.results.filter((r) => !r.ok);
        const ok = result.results.length - failed.length;
        if (result.dryRun) {
          toast.info(`Dry-run: ${ok} baja(s) simulada(s)${failed.length > 0 ? `, ${failed.length} error(es)` : ""}.`);
        } else if (failed.length === 0) {
          toast.success(`${ok} equipo(s) dado(s) de baja en SDS.`);
        } else {
          // Motivo real por equipo, no solo el conteo — sin esto es imposible saber
          // desde la UI si rechazó por no ser candidato o por una falla real de baja.
          const detail = failed.map((r) => `${r.serial}: ${r.error ?? "error desconocido"}`).join(" · ");
          toast.warning(`${ok} baja(s) OK, ${failed.length} error(es) — ${detail}`, { duration: 8000 });
        }
        await refresh(true);
        return true;
      } catch (err: unknown) {
        toast.error(errorMessage(err, "Error al dar de baja los equipos en SDS."));
        return false;
      } finally {
        if (mounted.current) setDeleting(false);
      }
    },
    [refresh],
  );

  return {
    rows,
    outages,
    candidateCount,
    loading,
    loadError,
    lastUpdatedAt,
    verifying,
    deleting,
    busyDeviceId,
    refresh,
    setDismissed,
    verify,
    deleteDevices,
  };
}
