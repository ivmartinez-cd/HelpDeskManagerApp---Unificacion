"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { despachadosApi } from "../api/despachados-api";
import type { ResumenDespachos } from "../types/despachados";
import { mensajeDeError } from "./use-despachados-listado";

/** Tarjetas de Despachados (`/resumen`, lectura barata de la base de HDM):
 * se recargan después de una acción o de "Actualizar ahora". */

export interface DespachadosTableroState {
  resumen: ResumenDespachos | null;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

export function useDespachadosTablero(): DespachadosTableroState {
  const [resumen, setResumen] = useState<ResumenDespachos | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const runToken = useRef(0);

  const reload = useCallback(async () => {
    const token = ++runToken.current;
    setLoading(true);
    try {
      const nuevoResumen = await despachadosApi.getResumen();
      if (token !== runToken.current) return;
      setResumen(nuevoResumen);
      setError(null);
    } catch (err) {
      if (token !== runToken.current) return;
      setError(mensajeDeError(err, "No se pudo cargar el resumen de despachos"));
    } finally {
      if (token === runToken.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- carga inicial, mismo patrón que use-historial-pending-orders
    void reload();
  }, [reload]);

  return { resumen, loading, error, reload };
}
