"use client";

import { useCallback, useEffect, useState } from "react";
import { watiApi } from "../api/wati-api";
import type { ConversacionPendiente, WatiPendientesResumen } from "../types/wati";

export interface WatiPendientesState {
  resumen: WatiPendientesResumen | null;
  pendientes: ConversacionPendiente[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

const REFRESH_MS = 60 * 1000;

/** Resumen + detalle de chats de WhatsApp esperando respuesta, refrescados
 * solos cada minuto (el backend los sincroniza contra WATI cada pocos
 * minutos; acá solo se relee el estado, no se llama a WATI). El refresco
 * periódico no vuelve a poner `loading` para que la card no parpadee —
 * mismo patrón que `useRemote` de Inicio: un `tick` dispara el efecto. */
export function useWatiPendientes(enabled: boolean): WatiPendientesState {
  const [tick, setTick] = useState(0);
  const [resumen, setResumen] = useState<WatiPendientesResumen | null>(null);
  const [pendientes, setPendientes] = useState<ConversacionPendiente[]>([]);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) return;
    let alive = true;
    Promise.all([watiApi.getResumen(), watiApi.listPendientes()])
      .then(([r, p]) => {
        if (!alive) return;
        setResumen(r);
        setPendientes(p);
        setError(null);
        setLoading(false);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar los chats de WhatsApp pendientes:", err);
        if (!alive) return;
        setError(
          err instanceof Error ? err.message : "No se pudieron cargar los chats pendientes.",
        );
        setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [enabled, tick]);

  useEffect(() => {
    if (!enabled) return;
    const id = setInterval(() => setTick((t) => t + 1), REFRESH_MS);
    return () => clearInterval(id);
  }, [enabled]);

  const refetch = useCallback(() => setTick((t) => t + 1), []);
  return { resumen, pendientes, loading, error, refetch };
}
