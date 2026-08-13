"use client";

import { useMemo, useState } from "react";
import { useSession } from "@/services/session-provider";
import { Spinner } from "@/shared/components/ui/spinner";
import { useCalendarioEvents } from "../hooks/use-calendario-events";
import { cleanTitle, formatDateLocal, getMonthDateRange, getMonthNameCapitalized } from "../utils/calendario-format";
import { CalendarioHeader } from "./calendario-header";
import { CalendarioMonthGrid, type GridDay } from "./calendario-month-grid";
import { EventDetailModal } from "./event-detail-modal";
import type { CalendarioVerPor } from "../types/calendario";

function buildGridDays(startDate: string): GridDay[] {
  const parts = startDate.split("-");
  const year = parseInt(parts[0], 10) || new Date().getFullYear();
  const month = (parseInt(parts[1], 10) || new Date().getMonth() + 1) - 1;

  const firstDayOfMonth = new Date(year, month, 1);
  let dayOfWeek = firstDayOfMonth.getDay() - 1; // 0=Mon, 6=Sun
  if (dayOfWeek === -1) dayOfWeek = 6;

  const gridStart = new Date(year, month, 1 - dayOfWeek);
  const days: GridDay[] = [];

  const todayStr = formatDateLocal(new Date());
  const curr = new Date(gridStart);

  const totalDaysInMonth = new Date(year, month + 1, 0).getDate();
  const totalCells = dayOfWeek + totalDaysInMonth > 35 ? 42 : 35;

  for (let i = 0; i < totalCells; i++) {
    const dateStr = formatDateLocal(curr);
    days.push({
      dateStr,
      dayNum: curr.getDate(),
      isCurrentMonth: curr.getMonth() === month,
      isToday: dateStr === todayStr,
    });
    curr.setDate(curr.getDate() + 1);
  }
  return days;
}

export function CalendarioTool() {
  const { user } = useSession();
  const defaultDates = useMemo(() => getMonthDateRange(0), []);
  const {
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    operadorId,
    setOperadorId,
    operadores,
    events,
    loading,
    error,
    selectedEvent,
    setSelectedEvent,
    refetch,
    syncing,
    syncError,
    lastSyncedAt,
    sync,
  } = useCalendarioEvents({
    initialStart: defaultDates.startStr,
    initialEnd: defaultDates.endStr,
    canFilterByOperador: user.isSuperadmin,
  });

  const [searchQuery, setSearchQuery] = useState<string>("");
  const [showFilterPanel, setShowFilterPanel] = useState<boolean>(false);
  const [verPor, setVerPor] = useState<CalendarioVerPor>("efectivo");

  const handlePrevMonth = () => {
    const parts = startDate.split("-");
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const prevFirst = new Date(year, month - 1, 1);
      const prevLast = new Date(year, month, 0);
      setStartDate(formatDateLocal(prevFirst));
      setEndDate(formatDateLocal(prevLast));
    }
  };

  const handleNextMonth = () => {
    const parts = startDate.split("-");
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const nextFirst = new Date(year, month + 1, 1);
      const nextLast = new Date(year, month + 2, 0);
      setStartDate(formatDateLocal(nextFirst));
      setEndDate(formatDateLocal(nextLast));
    }
  };

  const handleToday = () => {
    const currentDates = getMonthDateRange(0);
    setStartDate(currentDates.startStr);
    setEndDate(currentDates.endStr);
  };

  const handleExportCsv = () => {
    if (events.length === 0) return;
    const headers = ["Fecha", "Cliente", "Tipo Evento", "Sucursal Entrega", "Vendedor", "Detalle"];
    const rows = events.map((e) => [
      e.start ? e.start.split("T")[0] : "",
      `"${(e.cliente || "").replace(/"/g, '""')}"`,
      `"${(e.string_tipo_evento || "").replace(/"/g, '""')}"`,
      `"${(e.sucursal_entrega || "").replace(/"/g, '""')}"`,
      `"${(e.vendedor || "").replace(/"/g, '""')}"`,
      `"${cleanTitle(e.title).replace(/"/g, '""')}"`,
    ]);

    const csvContent = "\uFEFF" + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `planificacion_facturacion_${startDate}_${endDate}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredEvents = useMemo(() => {
    return events.filter((e) => {
      const titleClean = cleanTitle(e.title);
      const matchSearch =
        !searchQuery ||
        (e.cliente && e.cliente.toLowerCase().includes(searchQuery.toLowerCase())) ||
        titleClean.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (e.sucursal_entrega && e.sucursal_entrega.toLowerCase().includes(searchQuery.toLowerCase()));

      return matchSearch;
    });
  }, [events, searchQuery]);

  const eventsByDayMap = useMemo(() => {
    const map = new Map<string, typeof filteredEvents>();
    for (const evt of filteredEvents) {
      if (!evt.start) continue;
      const dayKey = evt.start.split("T")[0];
      if (!map.has(dayKey)) {
        map.set(dayKey, []);
      }
      map.get(dayKey)!.push(evt);
    }
    return map;
  }, [filteredEvents]);

  const gridDays = useMemo(() => buildGridDays(startDate), [startDate]);
  const currentMonthTitle = useMemo(() => getMonthNameCapitalized(startDate), [startDate]);

  return (
    <div className="flex flex-col gap-4 bg-background p-2 text-foreground">
      <CalendarioHeader
        currentMonthTitle={currentMonthTitle}
        onPrevMonth={handlePrevMonth}
        onNextMonth={handleNextMonth}
        onToday={handleToday}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        showFilterPanel={showFilterPanel}
        onToggleFilterPanel={() => setShowFilterPanel(!showFilterPanel)}
        onExportCsv={handleExportCsv}
        exportDisabled={events.length === 0}
        startDate={startDate}
        setStartDate={setStartDate}
        endDate={endDate}
        setEndDate={setEndDate}
        showOperadorFilter={user.isSuperadmin}
        operadorId={operadorId}
        setOperadorId={setOperadorId}
        operadores={operadores}
        onApplyFilters={refetch}
        loading={loading}
        syncing={syncing}
        onSync={sync}
        lastSyncedAt={lastSyncedAt}
        verPor={verPor}
        setVerPor={setVerPor}
      />

      {syncError && (
        <div className="rounded-xl border border-destructive/50 bg-destructive/10 p-3 text-xs text-destructive">
          {syncError}
        </div>
      )}

      {loading ? (
        <div className="flex h-96 items-center justify-center rounded-xl border border-border bg-card">
          <Spinner />
        </div>
      ) : error ? (
        <div className="rounded-xl border border-destructive/50 bg-destructive/10 p-4 text-xs text-destructive">
          {error}
        </div>
      ) : (
        <>
          <CalendarioMonthGrid
            gridDays={gridDays}
            eventsByDayMap={eventsByDayMap}
            onSelectEvent={setSelectedEvent}
            verPor={verPor}
          />
          {filteredEvents.some((e) => e.cobertura) && (
            <div className="flex items-center gap-4 px-1 font-body text-[11px] text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-full bg-brand-orange" />
                Evento cubierto (operador efectivo)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-full bg-brand-gray" />
                Evento propio
              </span>
            </div>
          )}
        </>
      )}

      <EventDetailModal event={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </div>
  );
}
