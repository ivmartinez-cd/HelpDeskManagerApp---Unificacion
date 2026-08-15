"use client";

import { ChevronDown, ChevronUp } from "lucide-react";
import { type ReactNode, useEffect, useState } from "react";
import type { AnalysisResult, Severity } from "../types/analisis-log-hp";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";
import {
  SEV_COLOR,
  filterIncidentsBySeverity,
  fmtDatetime,
  normSev,
} from "../utils/analysis-utils";

interface Props {
  analysis: AnalysisResult;
  deviceId: string | null;
  activeSeverities: Set<Severity>;
}

interface SectionProps {
  title: string;
  color: string;
  count: number;
  children: ReactNode;
}

function Section({ title, color, count, children }: SectionProps) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-border last:border-0">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-3 w-full py-3 text-left"
      >
        <div className="h-2 w-2 flex-none rounded-full" style={{ backgroundColor: color }} />
        <span className="font-body text-[13px] font-semibold text-foreground flex-1">{title}</span>
        <span className="font-body text-[12px] text-muted-foreground">{count}</span>
        {open ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground flex-none" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground flex-none" />
        )}
      </button>
      {open && <div className="pb-4">{children}</div>}
    </div>
  );
}

function IncidentsTable({ analysis, activeSeverities }: { analysis: AnalysisResult; activeSeverities: Set<Severity> }) {
  const visible = filterIncidentsBySeverity(analysis.incidents, activeSeverities);
  if (!visible.length) return <p className="font-body text-[13px] text-muted-foreground">Sin incidentes.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left" style={{ minWidth: 480 }}>
        <thead>
          <tr className="border-b border-border/50">
            {["Código", "Severidad", "Ocurrencias", "Inicio", "Fin"].map((h) => (
              <th key={h} className="py-1.5 pr-4 font-body text-[10px] font-bold uppercase tracking-wide text-muted-foreground">{h}</th>
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

function EventsTable({ analysis }: { analysis: AnalysisResult }) {
  const events = [...analysis.events].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  ).slice(0, 100);
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left" style={{ minWidth: 540 }}>
        <thead>
          <tr className="border-b border-border/50">
            {["Timestamp", "Código", "Tipo", "Contador"].map((h) => (
              <th key={h} className="py-1.5 pr-4 font-body text-[10px] font-bold uppercase tracking-wide text-muted-foreground">{h}</th>
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
      {analysis.events.length > 100 && (
        <p className="mt-2 font-body text-[11px] text-muted-foreground">
          Mostrando 100 de {analysis.events.length} eventos.
        </p>
      )}
    </div>
  );
}

function ConsumablesPanel({ deviceId }: { deviceId: string }) {
  const [data, setData] = useState<Record<string, unknown>[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!loaded) return;
    setLoading(true);
    analisisLogHpApi.getConsumables(Number(deviceId))
      .then(setData)
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [deviceId, loaded]);

  if (!loaded) return (
    <button
      type="button"
      onClick={() => setLoaded(true)}
      className="font-body text-[12px] text-brand-orange hover:underline"
    >
      Cargar estado de consumibles →
    </button>
  );
  if (loading) return <p className="font-body text-[13px] text-muted-foreground">Cargando...</p>;
  if (!data?.length) return <p className="font-body text-[13px] text-muted-foreground">Sin datos de consumibles.</p>;
  return (
    <pre className="font-mono text-[11px] text-foreground/70 overflow-auto max-h-48">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

export function AnalysisCollapsibles({ analysis, deviceId, activeSeverities }: Props) {
  const visible = filterIncidentsBySeverity(analysis.incidents, activeSeverities);
  return (
    <div className="rounded-[12px] border border-border bg-card px-4">
      <div className="py-3 font-body text-[10px] font-bold uppercase tracking-[.05em] text-muted-foreground">
        ANÁLISIS DETALLADO
      </div>

      <Section title="Incidencias detectadas" color={SEV_COLOR.ERROR} count={visible.length}>
        <IncidentsTable analysis={analysis} activeSeverities={activeSeverities} />
      </Section>

      <Section title="Eventos del período" color={SEV_COLOR.INFO} count={analysis.events_count}>
        <EventsTable analysis={analysis} />
      </Section>

      <Section
        title="Estado de consumibles en tiempo real"
        color={SEV_COLOR.WARNING}
        count={0}
      >
        {deviceId && deviceId !== "manual" ? (
          <ConsumablesPanel deviceId={deviceId} />
        ) : (
          <p className="font-body text-[13px] text-muted-foreground">
            No disponible para análisis manual.
          </p>
        )}
      </Section>
    </div>
  );
}
