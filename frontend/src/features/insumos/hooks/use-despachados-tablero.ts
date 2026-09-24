"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { despachadosApi } from "../api/despachados-api";
import type { FilaDespacho, ResumenDespachos } from "../types/despachados";
import { mensajeDeError } from "./use-despachados-listado";

/** Parte de arriba de Despachados: tarjetas (`/resumen`) y bandeja
 * "Requieren acción" (`/requieren-accion`, sin paginar, en el orden del
 * backend). Las dos lecturas son de la base de HDM, baratas: se piden juntas
 * y se recargan juntas después de una acción o de "Actualizar ahora". */

export interface DespachadosTableroState {
  resumen: ResumenDespachos | null;
  bandeja: FilaDespacho[];
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

export function useDespachadosTablero(): DespachadosTableroState {
  const [resumen, setResumen] = useState<ResumenDespachos | null>(null);
  const [bandeja, setBandeja] = useState<FilaDespacho[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const runToken = useRef(0);

  const reload = useCallback(async () => {
    const token = ++runToken.current;
    setLoading(true);
    try {
      const [nuevoResumen, filas] = await Promise.all([
        despachadosApi.getResumen(),
        despachadosApi.listarRequierenAccion(),
      ]);
      if (token !== runToken.current) return;
      setResumen(nuevoResumen);
      setBandeja(filas);
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

  return { resumen, bandeja, loading, error, reload };
}
