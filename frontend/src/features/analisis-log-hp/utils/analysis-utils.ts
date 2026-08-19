import type { Incident, LogEvent, Severity } from "../types/analisis-log-hp";

export const SEV_ORDER: Record<Severity, number> = {
  ERROR: 3,
  WARNING: 2,
  INFO: 1,
  UNKNOWN: 0,
};

export const SEV_COLOR: Record<Severity, string> = {
  ERROR: "#ef4444",
  WARNING: "#eab308",
  INFO: "#3b82f6",
  UNKNOWN: "#6b7280",
};

export const SEV_LABEL: Record<Severity, string> = {
  ERROR: "ERROR",
  WARNING: "WARNING",
  INFO: "INFO",
  UNKNOWN: "INFO",
};

export function normSev(s: string | null | undefined): Severity {
  if (s === "ERROR" || s === "WARNING" || s === "INFO") return s;
  return "UNKNOWN";
}

export function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "hace un momento";
  if (m < 60) return `hace ${m} min`;
  const h = Math.floor(m / 60);
  if (h < 24) return `hace ${h} h`;
  const d = Math.floor(h / 24);
  return `hace ${d} d`;
}

export function fmtDatetime(iso: string): string {
  return new Date(iso).toLocaleString("es-AR", {
    day: "2-digit", month: "2-digit", year: "2-digit",
    hour: "2-digit", minute: "2-digit",
  });
}

/** KPI: último error crítico (más reciente con severity ERROR) */
export function lastCriticalIncident(incidents: Incident[]): Incident | null {
  const errors = incidents.filter((i) => normSev(i.severity) === "ERROR");
  if (!errors.length) return null;
  return errors.reduce((a, b) =>
    new Date(a.end_time) > new Date(b.end_time) ? a : b
  );
}

/** KPI: tasa de errores — páginas por error (denominador = eventos ERROR, no incidentes) */
export function computeErrorRate(events: LogEvent[]): {
  label: string;
  labelColor?: string;
  sub: string;
  pagesInPeriod: number;
  totalCounter: number;
} {
  const counters = events.map((e) => e.counter).filter((c) => c > 0);
  if (counters.length < 2) {
    return { label: "—", sub: "sin datos de contador", pagesInPeriod: 0, totalCounter: 0 };
  }
  const cMin = Math.min(...counters);
  const cMax = Math.max(...counters);
  const pagesInPeriod = cMax - cMin;
  if (pagesInPeriod === 0) {
    return { label: "—", sub: "sin rango de contador", pagesInPeriod: 0, totalCounter: cMax };
  }

  const errorEvents = events.filter((e) => normSev(e.type) === "ERROR");
  const errorCount = errorEvents.length;
  if (errorCount === 0) {
    return {
      label: "Sin errores",
      labelColor: "var(--color-success, #22c55e)",
      sub: "sin errores críticos",
      pagesInPeriod,
      totalCounter: cMax,
    };
  }

  const freq = new Map<string, number>();
  for (const e of errorEvents) freq.set(e.code, (freq.get(e.code) ?? 0) + 1);
  const topCode = [...freq.entries()].reduce((a, b) => (b[1] > a[1] ? b : a))[0];

  const pagesPerError = Math.round(pagesInPeriod / errorCount);
  const label =
    pagesPerError >= 1
      ? `1 c/${pagesPerError.toLocaleString("es-AR")} pág.`
      : `${errorCount} err.`;
  return { label, sub: topCode, pagesInPeriod, totalCounter: cMax };
}

/** Datos del heatmap: día-de-semana × franja horaria → conteo */
export function buildHeatmapData(events: LogEvent[]): {
  matrix: number[][];
  days: string[];
  hours: number[];
  maxValue: number;
} {
  const days = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];
  const hours = [0, 3, 6, 9, 12, 15, 18, 21];
  const matrix: number[][] = Array.from({ length: 7 }, () => Array(8).fill(0));
  for (const ev of events) {
    const d = new Date(ev.timestamp);
    const dow = d.getDay();
    const slot = Math.floor(d.getHours() / 3);
    matrix[dow][slot]++;
  }
  const maxValue = Math.max(...matrix.flat(), 1);
  return { matrix, days, hours, maxValue };
}

/** Datos del chart de volumen por día: labels + datasets por severity */
export function buildVolumeChartData(events: LogEvent[]): {
  labels: string[];
  errors: number[];
  warnings: number[];
  infos: number[];
} {
  if (!events.length) return { labels: [], errors: [], warnings: [], infos: [] };

  const byDay: Map<string, { e: number; w: number; i: number }> = new Map();
  for (const ev of events) {
    const day = ev.timestamp.slice(0, 10);
    const cur = byDay.get(day) ?? { e: 0, w: 0, i: 0 };
    const sev = normSev(ev.code_severity);
    if (sev === "ERROR") cur.e++;
    else if (sev === "WARNING") cur.w++;
    else cur.i++;
    byDay.set(day, cur);
  }

  const sorted = [...byDay.entries()].sort(([a], [b]) => a.localeCompare(b));
  return {
    labels: sorted.map(([d]) => {
      const parts = d.split("-");
      return `${parts[2]}/${parts[1]}`;
    }),
    errors: sorted.map(([, v]) => v.e),
    warnings: sorted.map(([, v]) => v.w),
    infos: sorted.map(([, v]) => v.i),
  };
}

/** Datos del chart de errores más frecuentes (top 8 por code) */
export function buildFrequencyChartData(incidents: Incident[]): {
  labels: string[];
  counts: number[];
  colors: string[];
} {
  const grouped: Map<string, { count: number; sev: Severity }> = new Map();
  for (const inc of incidents) {
    const sev = normSev(inc.severity);
    const cur = grouped.get(inc.code);
    if (cur) {
      cur.count += inc.occurrences;
      if (SEV_ORDER[sev] > SEV_ORDER[cur.sev]) cur.sev = sev;
    } else {
      grouped.set(inc.code, { count: inc.occurrences, sev });
    }
  }
  const sorted = [...grouped.entries()]
    .sort(([, a], [, b]) => b.count - a.count)
    .slice(0, 8);
  return {
    labels: sorted.map(([code]) => code),
    counts: sorted.map(([, v]) => v.count),
    colors: sorted.map(([, v]) => SEV_COLOR[v.sev]),
  };
}

/** Filtra eventos por rango de días (0 = todos) */
export function filterEventsByDays(events: LogEvent[], days: number): LogEvent[] {
  if (days === 0) return events;
  const cutoff = Date.now() - days * 86400000;
  return events.filter((e) => new Date(e.timestamp).getTime() >= cutoff);
}

/** Filtra eventos por severity activa */
export function filterEventsBySeverity(
  events: LogEvent[],
  active: Set<Severity>,
): LogEvent[] {
  if (!active.size) return events;
  return events.filter((e) => active.has(normSev(e.code_severity)));
}

/** Filtra incidentes por severity activa */
export function filterIncidentsBySeverity(
  incidents: Incident[],
  active: Set<Severity>,
): Incident[] {
  if (!active.size) return incidents;
  return incidents.filter((i) => active.has(normSev(i.severity)));
}
