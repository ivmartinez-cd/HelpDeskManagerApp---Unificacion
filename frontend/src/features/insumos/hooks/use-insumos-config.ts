"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { insumosApi } from "../api/insumos-api";
import type { InsumosConfig, InsumosConfigPayload } from "../types";

/** Carga y guardado de los parámetros de operación (`/api/insumos/config`).
 *
 * TRAMPA del contrato: el PUT responde **200 aunque la validación de negocio
 * falle**, con `{ok:false, error}` en el body — `httpClient` no tira `ApiError`
 * en ese caso. Hay que ramificar por `result.ok`, y el `catch` queda solo para
 * fallas reales de red/servidor. */

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

export function useInsumosConfig() {
  const [config, setConfig] = useState<InsumosConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const mounted = useRef(false);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await insumosApi.getConfig();
      if (!mounted.current) return;
      setConfig(data);
      setLoadError(null);
    } catch (err: unknown) {
      if (!mounted.current) return;
      const message = errorMessage(err, "No se pudo cargar la configuración.");
      setLoadError(message);
      toast.error(message);
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Carga inicial: `load` prende el spinner en forma síncrona a propósito
    // (misma convención que `useCalendarioEvents` de contadores), para no
    // pintar el formulario vacío antes de tener los valores reales.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  /** Devuelve `true` solo si el backend confirmó el guardado. */
  const save = useCallback(async (payload: InsumosConfigPayload): Promise<boolean> => {
    setSaving(true);
    setSaveError(null);
    try {
      const result = await insumosApi.saveConfig(payload);
      if (!result.ok) {
        const message = result.error ?? "El backend rechazó la configuración.";
        if (mounted.current) setSaveError(message);
        toast.error(message);
        return false;
      }
      // Se relee en vez de asumir el payload: el backend normaliza (recorta
      // los mails, aplica defaults de campos ausentes) y queremos que el
      // formulario refleje lo que quedó grabado de verdad.
      const fresh = await insumosApi.getConfig();
      if (mounted.current) setConfig(fresh);
      toast.success("Configuración guardada.");
      return true;
    } catch (err: unknown) {
      const message = errorMessage(err, "No se pudo guardar la configuración.");
      if (mounted.current) setSaveError(message);
      toast.error(message);
      return false;
    } finally {
      if (mounted.current) setSaving(false);
    }
  }, []);

  return { config, loading, loadError, saving, saveError, save, reload: load };
}
