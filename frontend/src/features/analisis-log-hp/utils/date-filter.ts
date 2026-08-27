import type { DateRangePreset } from "@/shared/components/ui/date-range-picker";
import type { DateRange } from "@/shared/types/date-range";
import type { Incident, LogEvent } from "../types/analisis-log-hp";

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

/** Presets propios (no los de Insumos, `DEFAULT_PRESETS`): semanas y meses de
 * calendario completos en vez de "hasta hoy", más los rolling que no tienen
 * equivalente ahí (`ultimos-7`/`ultimos-30`) -- mismo comportamiento que el
 * filtro anterior de esta pantalla, solo con la UI compartida del Patrón 4. */
export const ANALISIS_LOG_HP_PRESETS: DateRangePreset[] = [
  {
    key: "hoy",
    label: "Hoy",
    range: () => {
      const now = new Date();
      return { startDate: fmt(now), endDate: fmt(now) };
    },
  },
  {
    key: "semana",
    label: "Esta semana",
    range: () => {
      const mon = mondayOf(new Date());
      return { startDate: fmt(mon), endDate: fmt(addDays(mon, 6)) };
    },
  },
  {
    key: "semana-pasada",
    label: "Semana anterior",
    range: () => {
      const mon = mondayOf(addDays(new Date(), -7));
      return { startDate: fmt(mon), endDate: fmt(addDays(mon, 6)) };
    },
  },
  {
    key: "mes",
    label: "Este mes",
    range: () => {
      const now = new Date();
      return { startDate: fmt(new Date(now.getFullYear(), now.getMonth(), 1)), endDate: fmt(now) };
    },
  },
  {
    key: "mes-pasado",
    label: "Mes anterior",
    range: () => {
      const now = new Date();
      const lm = new Date(now.getFullYear(), now.getMonth() - 1, 1);
      return { startDate: fmt(lm), endDate: fmt(new Date(lm.getFullYear(), lm.getMonth() + 1, 0)) };
    },
  },
  {
    key: "ultimos-7",
    label: "Últimos 7 días",
    range: () => {
      const now = new Date();
      return { startDate: fmt(addDays(now, -6)), endDate: fmt(now) };
    },
  },
  {
    key: "ultimos-30",
    label: "Últimos 30 días",
    range: () => {
      const now = new Date();
      return { startDate: fmt(addDays(now, -29)), endDate: fmt(now) };
    },
  },
];

/** Ventana [minTs, maxTs] en ms, o null si no hay rango elegido ("todo el
 * período" -- el `DateRangePicker` compartido lo representa con `null`,
 * botón "Limpiar"). */
export function dateRangeWindow(range: DateRange | null): { minTs: number; maxTs: number } | null {
  if (!range) return null;
  const [sy, sm, sd] = range.startDate.split("-").map(Number);
  const [ey, em, ed] = range.endDate.split("-").map(Number);
  return {
    minTs: new Date(sy, sm - 1, sd, 0, 0, 0, 0).getTime(),
    maxTs: new Date(ey, em - 1, ed, 23, 59, 59, 999).getTime(),
  };
}

export function filterEventsByDateRange(events: LogEvent[], range: DateRange | null): LogEvent[] {
  const window = dateRangeWindow(range);
  if (!window) return events;
  return events.filter((e) => {
    const t = new Date(e.timestamp).getTime();
    return t >= window.minTs && t <= window.maxTs;
  });
}

/** Incidente visible si su ventana [start_time, end_time] pisa el rango filtrado. */
export function filterIncidentsByDateRange(incidents: Incident[], range: DateRange | null): Incident[] {
  const window = dateRangeWindow(range);
  if (!window) return incidents;
  return incidents.filter((i) => {
    const s = new Date(i.start_time).getTime();
    const e = new Date(i.end_time).getTime();
    return e >= window.minTs && s <= window.maxTs;
  });
}

