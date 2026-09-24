"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { despachadosApi } from "../api/despachados-api";
import type { DetalleDespacho } from "../types/despachados";
import { mensajeDeError } from "./use-despachados-listado";

/** Detalle de la guía abierta en el panel lateral (`GET /despachados/{guia}`).
 * Con `guia = null` no pide nada. Al recargar (después de registrar una acción
 * o cerrar la alerta) mantiene el detalle anterior a la vista hasta que llega
 * el nuevo, para que el panel no parpadee. */

export interface DespachoDetalleState {
  detalle: DetalleDespacho | null;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

export function useDespachoDetalle(guia: string | null): DespachoDetalleState {
  const [detalle, setDetalle] = useState<DetalleDespacho | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const runToken = useRef(0);

  const cargar = useCallback(async (objetivo: string | null) => {
    const token = ++runToken.current;
    if (!objetivo) {
      setDetalle(null);
      setError(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const nuevo = await despachadosApi.getDetalle(objetivo);
      if (token !== runToken.current) return;
      setDetalle(nuevo);
      setError(null);
    } catch (err) {
      if (token !== runToken.current) return;
      setError(mensajeDeError(err, "No se pudo cargar el detalle de la guía"));
    } finally {
      if (token === runToken.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- carga al cambiar de guía, mismo patrón que use-historial-pending-orders
    void cargar(guia);
  }, [guia, cargar]);

  const reload = useCallback(() => cargar(guia), [cargar, guia]);

  // Mientras llega el detalle de otra guía, no mostrar el de la anterior.
  const vigente = detalle && detalle.envio.guia === guia ? detalle : null;
  return { detalle: vigente, loading, error, reload };
}
