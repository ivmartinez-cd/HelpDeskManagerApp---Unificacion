"use client";

import { useCallback, useEffect, useState } from "react";
import { notificacionesApi, type Notificacion } from "../api/notificaciones-api";

const REFRESH_MS = 30 * 1000;

export interface NoLeidasState {
  /** Las no leídas más recientes (hasta 20), para detectar las nuevas. */
  noLeidas: Notificacion[];
  /** Total de no leídas: el número del badge. */
  total: number;
  /** false hasta la primera respuesta: antes de eso `noLeidas` vacío no
   * significa "no hay". */
  cargado: boolean;
  refetch: () => void;
}

/** Relee las no leídas cada 30 s y al volver a la pestaña. Las genera el
 * backend (jobs de fondo), así que acá solo se consulta la bandeja, nunca un
 * sistema externo. Un error de red se loguea y se reintenta en el próximo
 * ciclo sin tocar lo que ya se mostraba. */
export function useNoLeidasPolling(): NoLeidasState {
  const [tick, setTick] = useState(0);
  const [noLeidas, setNoLeidas] = useState<Notificacion[]>([]);
  const [total, setTotal] = useState(0);
  const [cargado, setCargado] = useState(false);

  useEffect(() => {
    let alive = true;
    notificacionesApi
      .listar({ soloNoLeidas: true })
      .then((page) => {
        if (!alive) return;
        setNoLeidas(page.items);
        setTotal(page.total);
        setCargado(true);
      })
      .catch((err: unknown) => console.error("Error al cargar notificaciones:", err));
    return () => {
      alive = false;
    };
  }, [tick]);

  useEffect(() => {
    const refrescar = () => setTick((t) => t + 1);
    const alVolver = () => {
      if (document.visibilityState === "visible") refrescar();
    };
    const id = setInterval(refrescar, REFRESH_MS);
    document.addEventListener("visibilitychange", alVolver);
    return () => {
      clearInterval(id);
      document.removeEventListener("visibilitychange", alVolver);
    };
  }, []);

  const refetch = useCallback(() => setTick((t) => t + 1), []);
  return { noLeidas, total, cargado, refetch };
}
