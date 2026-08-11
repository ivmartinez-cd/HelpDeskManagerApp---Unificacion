"use client";

import { useCallback, useEffect, useState } from "react";
import { contadoresApi } from "../api/contadores-api";
import type { CalendarEvent } from "../types/calendario";

interface UseCalendarioEventsOptions {
  initialStart: string;
  initialEnd: string;
}

export function useCalendarioEvents({ initialStart, initialEnd }: UseCalendarioEventsOptions) {
  const [startDate, setStartDate] = useState<string>(initialStart);
  const [endDate, setEndDate] = useState<string>(initialEnd);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await contadoresApi.getCalendarioEvents({ start: startDate, end: endDate });
      setEvents(response.items);
      setTotal(response.total);
    } catch (err: unknown) {
      console.error("Error al cargar eventos del calendario:", err);
      setError(err instanceof Error ? err.message : "Error al cargar la planificación.");
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    // fetch-on-mount/on-filter-change; `fetchEvents` flips `loading`
    // synchronously on purpose so the grid doesn't render stale events.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchEvents();
  }, [fetchEvents]);

  useEffect(() => {
    contadoresApi
      .getSyncStatus()
      .then((status) => setLastSyncedAt(status.last_synced_at))
      .catch((err: unknown) => console.error("Error al consultar el estado de sync:", err));
  }, []);

  const sync = useCallback(async () => {
    setSyncing(true);
    setSyncError(null);
    try {
      const result = await contadoresApi.syncCalendario();
      setLastSyncedAt(result.synced_at);
      await fetchEvents();
    } catch (err: unknown) {
      console.error("Error al sincronizar el calendario:", err);
      setSyncError(err instanceof Error ? err.message : "Error al sincronizar con Gestión.");
    } finally {
      setSyncing(false);
    }
  }, [fetchEvents]);

  return {
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    events,
    total,
    loading,
    error,
    selectedEvent,
    setSelectedEvent,
    refetch: fetchEvents,
    syncing,
    syncError,
    lastSyncedAt,
    sync,
  };
}
