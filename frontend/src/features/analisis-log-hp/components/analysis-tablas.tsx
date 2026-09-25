"use client";

import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import { isoSortValue, useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";
import type { AnalysisResult, Incident, LogEvent, Severity } from "../types/analisis-log-hp";
import { SEV_COLOR, SEV_ORDER, filterIncidentsBySeverity, fmtDatetime, normSev } from "../utils/analysis-utils";

/** Tablas de incidentes y eventos del análisis, extraídas de
 * `analysis-collapsibles.tsx`. Arrancan en el orden de siempre y ordenan por
 * cualquier encabezado; Severidad ordena por gravedad, no alfabéticamente. */

const TH = "py-1.5 pr-4 font-body text-[10px] font-bold uppercase tracking-wide text-muted-foreground";
const MAX_EVENTOS = 100;

type IncidenteKey = "codigo" | "severidad" | "ocurrencias" | "inicio" | "fin";

const COLUMNAS_INCIDENTE: SortableColumn<IncidenteKey>[] = [
  { key: "codigo", label: "Código" },
  { key: "severidad", label: "Severidad" },
  { key: "ocurrencias", label: "Ocurrencias" },
  { key: "inicio", label: "Inicio" },
  { key: "fin", label: "Fin" },
];

const INCIDENTE_DESC_PRIMERO: readonly IncidenteKey[] = ["severidad", "ocurrencias", "inicio", "fin"];

function valorIncidente(inc: Incident, key: IncidenteKey) {
  switch (key) {
    case "codigo": return inc.code;
    case "severidad": return SEV_ORDER[normSev(inc.severity)];
    case "ocurrencias": return inc.occurrences;
    case "inicio": return isoSortValue(inc.start_time);
    case "fin": return isoSortValue(inc.end_time);
  }
}

export function IncidentsTable({ analysis, activeSeverities }: { analysis: AnalysisResult; activeSeverities: Set<Severity> }) {
  const { sort, toggleSort } = useOptionalTableSort(INCIDENTE_DESC_PRIMERO);
  const visible = useSortedRows(filterIncidentsBySeverity(analysis.incidents, activeSeverities), sort, valorIncidente);
  if (!visible.length) return <p className="font-body text-[13px] text-muted-foreground">Sin incidentes.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left" style={{ minWidth: 480 }}>
        <thead>
          <tr className="border-b border-border/50">
            {COLUMNAS_INCIDENTE.map((c) => (
              <SortableHeader key={c.key} column={c} sort={sort} onToggleSort={toggleSort} thClassName={TH} />
            ))}
          </tr>
        </thead>
        <tbody>
          {visible.map((inc) => {
            const sev = normSev(inc.severity);
            return (
              <tr key={inc.id} className="border-b border-border/30 hover:bg-white/[.02]">
                <td className="py-2 pr-4 font-mono text-[12px]" style={{ color: SEV_COLOR[sev] }}>{inc.code}</td>
                <td className="py-2 pr-4 font-body text-[11px]" style={{ color: SEV_COLOR[sev] }}>{sev}</td>
                <td className="py-2 pr-4 font-body text-[12px] text-foreground">{inc.occurrences}</td>
                <td className="py-2 pr-4 font-body text-[11px] text-muted-foreground">{fmtDatetime(inc.start_time)}</td>
                <td className="py-2 pr-4 font-body text-[11px] text-muted-foreground">{fmtDatetime(inc.end_time)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

type EventoKey = "timestamp" | "codigo" | "tipo" | "contador";

const COLUMNAS_EVENTO: SortableColumn<EventoKey>[] = [
  { key: "timestamp", label: "Timestamp" },
  { key: "codigo", label: "Código" },
  { key: "tipo", label: "Tipo" },
  { key: "contador", label: "Contador" },
];

const EVENTO_DESC_PRIMERO: readonly EventoKey[] = ["timestamp", "contador"];

function valorEvento(ev: LogEvent, key: EventoKey) {
  switch (key) {
    case "timestamp": return isoSortValue(ev.timestamp);
    case "codigo": return ev.code;
    case "tipo": return ev.type;
    case "contador": return ev.counter;
  }
}

/** Los 100 eventos más recientes (sin orden elegido, del más nuevo al más
 * viejo); el orden por columna reordena esos 100, no elige otros. */
function eventosRecientes(analysis: AnalysisResult): LogEvent[] {
  return [...analysis.events]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, MAX_EVENTOS);
}

export function EventsTable({ analysis }: { analysis: AnalysisResult }) {
  const { sort, toggleSort } = useOptionalTableSort(EVENTO_DESC_PRIMERO);
  const events = useSortedRows(eventosRecientes(analysis), sort, valorEvento);
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left" style={{ minWidth: 540 }}>
        <thead>
          <tr className="border-b border-border/50">
            {COLUMNAS_EVENTO.map((c) => (
              <SortableHeader key={c.key} column={c} sort={sort} onToggleSort={toggleSort} thClassName={TH} />
            ))}
          </tr>
        </thead>
        <tbody>
          {events.map((ev, i) => {
            const sev = normSev(ev.code_severity);
            return (
              <tr key={i} className="border-b border-border/30 hover:bg-white/[.02]">
                <td className="py-1.5 pr-4 font-mono text-[11px] text-muted-foreground">{fmtDatetime(ev.timestamp)}</td>
                <td className="py-1.5 pr-4 font-mono text-[12px]" style={{ color: SEV_COLOR[sev] }}>{ev.code}</td>
                <td className="py-1.5 pr-4 font-body text-[11px] text-muted-foreground">{ev.type}</td>
                <td className="py-1.5 pr-4 font-body text-[11px] text-foreground">{ev.counter.toLocaleString("es-AR")}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {analysis.events.length > MAX_EVENTOS && (
        <p className="mt-2 font-body text-[11px] text-muted-foreground">
          Mostrando {MAX_EVENTOS} de {analysis.events.length} eventos.
        </p>
      )}
    </div>
  );
}
