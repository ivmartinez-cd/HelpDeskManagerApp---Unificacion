import type { Incident, LogEvent } from "../types/analisis-log-hp";

export type DateFilterPreset =
  | "all"
  | "today"
  | "week"
  | "last-week"
  | "month"
  | "last-month"
  | "last-7"
  | "last-30";

export type DateFilterRange = { start: string; end: string }; // YYYY-MM-DD, inclusive
export type DateFilter = DateFilterPreset | DateFilterRange;

export const PRESET_OPTIONS: { value: DateFilterPreset; label: string }[] = [
  { value: "all", label: "Todo el período" },
  { value: "today", label: "Hoy" },
  { value: "week", label: "Esta semana" },
  { value: "last-week", label: "Semana anterior" },
  { value: "month", label: "Este mes" },
  { value: "last-month", label: "Mes anterior" },
  { value: "last-7", label: "Últimos 7 días" },
  { value: "last-30", label: "Últimos 30 días" },
];

const fmt = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

function addDays(d: Date, n: number): Date {
  const r = new Date(d);
  r.setDate(r.getDate() + n);
  return r;
}

/** Lunes de la semana de `d` (weekStartsOn=1, como el legacy). */
function mondayOf(d: Date): Date {
  const day = d.getDay();
  return addDays(d, day === 0 ? -6 : 1 - day);
}

function presetToRange(preset: Exclude<DateFilterPreset, "all">): DateFilterRange {
  const now = new Date();
  if (preset === "today") return { start: fmt(now), end: fmt(now) };
  if (preset === "week") {
    const mon = mondayOf(now);
    return { start: fmt(mon), end: fmt(addDays(mon, 6)) };
  }
  if (preset === "last-week") {
    const mon = mondayOf(addDays(now, -7));
    return { start: fmt(mon), end: fmt(addDays(mon, 6)) };
  }
  if (preset === "month") {
    return { start: fmt(new Date(now.getFullYear(), now.getMonth(), 1)), end: fmt(now) };
  }
  if (preset === "last-month") {
    const lm = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    return { start: fmt(lm), end: fmt(new Date(lm.getFullYear(), lm.getMonth() + 1, 0)) };
  }
  if (preset === "last-7") return { start: fmt(addDays(now, -6)), end: fmt(now) };
  return { start: fmt(addDays(now, -29)), end: fmt(now) }; // last-30
}

/** Ventana [minTs, maxTs] en ms, o null si el filtro es "all". */
export function dateFilterWindow(filter: DateFilter): { minTs: number; maxTs: number } | null {
  if (filter === "all") return null;
  const range = typeof filter === "string" ? presetToRange(filter) : filter;
  const [sy, sm, sd] = range.start.split("-").map(Number);
  const [ey, em, ed] = range.end.split("-").map(Number);
  return {
    minTs: new Date(sy, sm - 1, sd, 0, 0, 0, 0).getTime(),
    maxTs: new Date(ey, em - 1, ed, 23, 59, 59, 999).getTime(),
  };
}

export function filterEventsByDateFilter(events: LogEvent[], filter: DateFilter): LogEvent[] {
  const window = dateFilterWindow(filter);
  if (!window) return events;
  return events.filter((e) => {
    const t = new Date(e.timestamp).getTime();
    return t >= window.minTs && t <= window.maxTs;
  });
}

/** Incidente visible si su ventana [start_time, end_time] pisa el rango filtrado. */
export function filterIncidentsByDateFilter(incidents: Incident[], filter: DateFilter): Incident[] {
  const window = dateFilterWindow(filter);
  if (!window) return incidents;
  return incidents.filter((i) => {
    const s = new Date(i.start_time).getTime();
    const e = new Date(i.end_time).getTime();
    return e >= window.minTs && s <= window.maxTs;
  });
}

export function dateFilterLabel(filter: DateFilter): string {
  const short = (s: string) => {
    const [y, m, d] = s.split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString("es-AR", { day: "numeric", month: "short" });
  };
  if (filter === "all") return "Todo el período";
  if (typeof filter === "string") {
    const preset = PRESET_OPTIONS.find((p) => p.value === filter);
    if (preset) {
      const range = presetToRange(filter);
      return `${preset.label} (${short(range.start)} – ${short(range.end)})`;
    }
  }
  const range = filter as DateFilterRange;
  return range.start === range.end ? short(range.start) : `${short(range.start)} – ${short(range.end)}`;
}
