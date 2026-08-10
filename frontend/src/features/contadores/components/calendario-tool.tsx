"use client";

import { useMemo, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Download,
  Filter,
  RefreshCw,
  Search,
} from "lucide-react";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { useCalendarioEvents } from "../hooks/use-calendario-events";
import { EventDetailModal } from "./event-detail-modal";
import type { CalendarEvent } from "../types/calendario";

function formatDateLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function getMonthDateRange(offsetMonths = 0) {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + offsetMonths;
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);

  return {
    startStr: formatDateLocal(firstDay),
    endStr: formatDateLocal(lastDay),
  };
}

function cleanTitle(title: string | null | undefined): string {
  if (!title) return "";
  return title.replace(/<[^>]*>/g, "").trim();
}

function getMonthNameCapitalized(dateStr: string): string {
  const parts = dateStr.split("-");
  if (parts.length >= 2) {
    const year = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1;
    const d = new Date(year, month, 1);
    const name = d.toLocaleDateString("es-AR", { month: "long", year: "numeric" });
    return name.charAt(0).toUpperCase() + name.slice(1);
  }
  return dateStr;
}

function getEventPillStyle(evt: CalendarEvent): string {
  const tipo = (evt.string_tipo_evento || "").toLowerCase();
  const title = (evt.title || "").toLowerCase();

  if (tipo.includes("facturaci") || title.includes("(facturaci")) {
    return "bg-[#ff9000] text-white hover:bg-[#e07f00]";
  }
  if (tipo.includes("vencimiento") || title.includes("(vencimiento")) {
    return "bg-[#d90077] text-white hover:bg-[#b80065]";
  }
  return "bg-[#343a40] text-white hover:bg-[#212529]";
}

const WEEKDAYS = ["LUN", "MAR", "MIÉR", "JUEV", "VIER", "SÁB", "DOM"];

export function CalendarioTool() {
  const defaultDates = useMemo(() => getMonthDateRange(0), []);
  const {
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    operadorId,
    setOperadorId,
    soloFacturacion,
    setSoloFacturacion,
    events,
    loading,
    error,
    selectedEvent,
    setSelectedEvent,
    refetch,
  } = useCalendarioEvents({
    initialStart: defaultDates.startStr,
    initialEnd: defaultDates.endStr,
    initialOperadorId: "318",
    initialSoloFacturacion: true,
  });

  const [searchQuery, setSearchQuery] = useState<string>("");
  const [showFilterPanel, setShowFilterPanel] = useState<boolean>(false);

  // Month navigation
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

  // CSV Export
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

  // Filtered Events
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

  // Group events by day string "YYYY-MM-DD"
  const eventsByDayMap = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
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

  // Grid calculation for full month calendar
  const gridDays = useMemo(() => {
    const parts = startDate.split("-");
    const year = parseInt(parts[0], 10) || new Date().getFullYear();
    const month = (parseInt(parts[1], 10) || (new Date().getMonth() + 1)) - 1;

    const firstDayOfMonth = new Date(year, month, 1);
    let dayOfWeek = firstDayOfMonth.getDay() - 1; // 0=Mon, 6=Sun
    if (dayOfWeek === -1) dayOfWeek = 6;

    const gridStart = new Date(year, month, 1 - dayOfWeek);
    const days: { dateStr: string; dayNum: number; isCurrentMonth: boolean; isToday: boolean }[] = [];

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
  }, [startDate]);

  const currentMonthTitle = useMemo(() => getMonthNameCapitalized(startDate), [startDate]);

  return (
    <div className="flex flex-col gap-4 bg-background p-2 text-foreground">
      {/* Top Header Bar matching Image 2 */}
      <div className="flex flex-wrap items-center justify-between gap-4 py-2">
        <div className="flex items-center gap-3">
          <h2 className="font-heading text-2xl font-extrabold tracking-tight text-foreground">
            {currentMonthTitle}
          </h2>

          <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1">
            <button
              onClick={handlePrevMonth}
              className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              title="Mes Anterior"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={handleNextMonth}
              className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              title="Mes Siguiente"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
            <button
              onClick={handleToday}
              className="ml-1 rounded px-2.5 py-1 text-xs font-semibold text-foreground hover:bg-muted transition-colors border border-border"
            >
              Hoy
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Search box */}
          <div className="relative w-48 sm:w-64">
            <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Buscar cliente..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-border bg-card pl-8 pr-3 py-1 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <button
            onClick={() => setShowFilterPanel(!showFilterPanel)}
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-muted transition-colors"
          >
            <Filter className="h-3.5 w-3.5 text-muted-foreground" />
            Filtros
          </button>

          {/* Export button */}
          <button
            onClick={handleExportCsv}
            disabled={events.length === 0}
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3.5 py-1.5 text-xs font-semibold text-foreground hover:bg-muted transition-colors disabled:opacity-50"
          >
            <Download className="h-3.5 w-3.5 text-muted-foreground" />
            Exportar
          </button>
        </div>
      </div>

      {/* Expandable Filter Panel */}
      {showFilterPanel && (
        <div className="flex flex-wrap items-center gap-4 rounded-xl border border-border bg-card p-4 text-xs">
          <BrandInput
            id="start-date"
            label="Desde"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-36 text-xs"
          />
          <BrandInput
            id="end-date"
            label="Hasta"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-36 text-xs"
          />
          <div className="w-32">
            <BrandInput
              id="operador-id"
              label="Operador ID"
              placeholder="Ej: 318"
              value={operadorId}
              onChange={(e) => setOperadorId(e.target.value)}
              className="text-xs"
            />
          </div>
          <div className="flex items-center gap-2 pt-5">
            <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-foreground">
              <input
                type="checkbox"
                checked={soloFacturacion}
                onChange={(e) => setSoloFacturacion(e.target.checked)}
                className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
              />
              Solo Facturación
            </label>
          </div>
          <div className="pt-5 ml-auto flex items-center gap-2">
            <BrandButton variant="outline" size="sm" onClick={refetch} disabled={loading}>
              <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Aplicar Filtros
            </BrandButton>
          </div>
        </div>
      )}

      {/* Main Calendar View Area */}
      {loading ? (
        <div className="flex h-96 items-center justify-center rounded-xl border border-border bg-card">
          <Spinner />
        </div>
      ) : error ? (
        <div className="rounded-xl border border-destructive/50 bg-destructive/10 p-4 text-xs text-destructive">
          {error}
        </div>
      ) : (
        <div className="flex flex-col border border-border rounded-xl bg-card shadow-sm overflow-hidden">
          {/* Weekday Labels Header Row */}
          <div className="grid grid-cols-7 border-b border-border bg-muted/40 text-center text-[11px] font-bold text-muted-foreground uppercase py-2.5">
            {WEEKDAYS.map((day) => (
              <div key={day} className="tracking-wider">
                {day}
              </div>
            ))}
          </div>

          {/* Month Calendar Days Grid (7 columns x 5-6 rows) */}
          <div className="grid grid-cols-7 divide-x divide-y divide-border bg-border/20">
            {gridDays.map((cell, index) => {
              const dayEvents = eventsByDayMap.get(cell.dateStr) || [];

              return (
                <div
                  key={`${cell.dateStr}-${index}`}
                  className={`flex flex-col min-h-[120px] p-1.5 transition-colors ${
                    cell.isCurrentMonth
                      ? "bg-card hover:bg-muted/20"
                      : "bg-muted/10 opacity-40 hover:opacity-60"
                  }`}
                >
                  {/* Cell Header: Day Number */}
                  <div className="flex items-center justify-between mb-1.5 px-1">
                    <span />
                    {cell.isToday ? (
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#ff9000] text-xs font-bold text-white shadow-sm">
                        {cell.dayNum}
                      </span>
                    ) : (
                      <span
                        className={`text-xs font-semibold ${
                          cell.isCurrentMonth
                            ? "text-foreground"
                            : "text-muted-foreground"
                        }`}
                      >
                        {cell.dayNum}
                      </span>
                    )}
                  </div>

                  {/* Day Events Pills List */}
                  <div className="flex flex-col gap-1 overflow-y-auto max-h-[140px] pr-0.5 scrollbar-thin">
                    {dayEvents.map((evt, evtIdx) => {
                      const pillStyle = getEventPillStyle(evt);
                      const displayLabel = cleanTitle(evt.title) || evt.cliente || "Facturación";

                      return (
                        <div
                          key={`${evt.id}-${cell.dateStr}-${evtIdx}`}
                          onClick={() => setSelectedEvent(evt)}
                          title={displayLabel}
                          className={`group cursor-pointer rounded-md px-2 py-1 text-[11px] font-bold leading-tight shadow-2xs transition-all ${pillStyle}`}
                        >
                          <div className="truncate">{displayLabel}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Event Detail Modal */}
      <EventDetailModal
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
      />
    </div>
  );
}
