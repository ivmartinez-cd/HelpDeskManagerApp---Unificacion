"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { insumosApi } from "../api/insumos-api";
import type { PendingOrderRow } from "../types";

/** Pedidos propios que siguen circulando en Canal Directo (pestaña "Pedidos
 * Pendientes" del Historial).
 *
 * Es el endpoint más caro del módulo (SOAP de Canal Directo + Insight en
 * paralelo), así que el polling de 90s corre **solo mientras la pestaña está
 * activa** y se frena también cuando la pestaña del navegador pasa a segundo
 * plano (al volver, refresca una vez y reanuda). Mismo criterio que el
 * `pending.start()/.stop()` del legacy, más el `visibilitychange` que el
 * legacy no tenía.
 *
 * No hay librería de fetching/polling en el proyecto: `setInterval` a mano.
 */

const POLL_INTERVAL_MS = 90_000;

export interface HistorialPendingOrdersState {
  orders: PendingOrderRow[];
  loading: boolean;
  error: string | null;
  /** Último refresco exitoso, para el "actualizado hace…" de la barra. */
  lastUpdated: Date | null;
  refresh: () => Promise<void>;
}

interface Options {
  /** La pestaña está a la vista: sin esto no se pide ni se pollea nada. */
  active: boolean;
  /** Suma los pedidos ya entregados — filtro REAL del endpoint
   * (`includeDelivered`), no client-side. */
  includeDelivered: boolean;
}

export function useHistorialPendingOrders({
  active,
  includeDelivered,
}: Options): HistorialPendingOrdersState {
  const [orders, setOrders] = useState<PendingOrderRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const runToken = useRef(0);

  const load = useCallback(
    async (silent: boolean) => {
      const token = ++runToken.current;
      if (!silent) setLoading(true);
      try {
        const page = await insumosApi.listPendingOrders({ includeDelivered });
        if (token !== runToken.current) return;
        setOrders(page.items);
        setLastUpdated(new Date());
        setError(null);
      } catch (err) {
        if (token !== runToken.current) return;
        // Un poll silencioso que falla no puede vaciar la tabla: se deja lo
        // último bueno y se avisa arriba.
        setError(err instanceof Error && err.message ? err.message : "No se pudieron cargar los pedidos pendientes");
      } finally {
        if (token === runToken.current && !silent) setLoading(false);
      }
    },
    [includeDelivered],
  );

  const refresh = useCallback(() => load(false), [load]);

  useEffect(() => {
    if (!active) return;

    let timer: number | undefined;
    const stop = () => {
      if (timer !== undefined) window.clearInterval(timer);
      timer = undefined;
    };
    const start = () => {
      stop();
      timer = window.setInterval(() => void load(true), POLL_INTERVAL_MS);
    };
    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        void load(true);
        start();
      } else {
        stop();
      }
    };

    void load(false);
    if (document.visibilityState === "visible") start();
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      stop();
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [active, load]);

  return { orders, loading, error, lastUpdated, refresh };
}
