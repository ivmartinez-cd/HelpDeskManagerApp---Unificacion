"use client";

import { useCallback, useEffect, useState } from "react";
import { contadoresApi } from "../api/contadores-api";
import type { CalendarEvent } from "../types/calendario";

interface UseCalendarioEventsOptions {
  initialStart: string;
  initialEnd: string;
  initialOperadorId?: string;
  initialSoloFacturacion?: boolean;
}

export function useCalendarioEvents({
  initialStart,
  initialEnd,
  initialOperadorId = "318",
  initialSoloFacturacion = true,
}: UseCalendarioEventsOptions) {
  const [startDate, setStartDate] = useState<string>(initialStart);
  const [endDate, setEndDate] = useState<string>(initialEnd);
  const [operadorId, setOperadorId] = useState<string>(initialOperadorId);
  const [soloFacturacion, setSoloFacturacion] = useState<boolean>(initialSoloFacturacion);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await contadoresApi.getCalendarioEvents({
        start: startDate,
        end: endDate,
        operador_id: operadorId || undefined,
        solo_facturacion: soloFacturacion,
      });
      setEvents(response.events);
      setTotal(response.total);
    } catch (err: unknown) {
      console.error("Error al cargar eventos del calendario:", err);
      setError(err instanceof Error ? err.message : "Error al cargar la planificación.");
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, operadorId, soloFacturacion]);


  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  return {
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    operadorId,
    setOperadorId,
    soloFacturacion,
    setSoloFacturacion,
    events,
    total,
    loading,
    error,
    selectedEvent,
    setSelectedEvent,
    refetch: fetchEvents,
  };
}
