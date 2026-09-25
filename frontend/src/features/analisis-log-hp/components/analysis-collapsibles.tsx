"use client";

import { ChevronDown, ChevronUp } from "lucide-react";
import { type ReactNode, useEffect, useState } from "react";
import type { AnalysisResult, Severity } from "../types/analisis-log-hp";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";
import { SEV_COLOR, filterIncidentsBySeverity } from "../utils/analysis-utils";
import { EventsTable, IncidentsTable } from "./analysis-tablas";
import { CdsIncidentsPanel } from "./cds-incidents-panel";
import { SdsAlertsPanel } from "./sds-alerts-panel";

interface Props {
  analysis: AnalysisResult;
  deviceId: string | null;
  serial: string;
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

function ConsumablesPanel({ deviceId }: { deviceId: string }) {
  const [result, setResult] = useState<{ deviceId: string; data: Record<string, unknown>[] } | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!loaded) return;
    let cancelled = false;
    analisisLogHpApi.getConsumables(Number(deviceId))
      .then((data) => { if (!cancelled) setResult({ deviceId, data }); })
      .catch(() => { if (!cancelled) setResult({ deviceId, data: [] }); });
    return () => { cancelled = true; };
  }, [deviceId, loaded]);

  const data = result?.deviceId === deviceId ? result.data : null;
  if (!loaded) return (
    <button
      type="button"
      onClick={() => setLoaded(true)}
      className="font-body text-[12px] text-brand-orange hover:underline"
    >
      Cargar estado de consumibles →
    </button>
  );
  if (data === null) return <p className="font-body text-[13px] text-muted-foreground">Cargando...</p>;
  if (!data.length) return <p className="font-body text-[13px] text-muted-foreground">Sin datos de consumibles.</p>;
  return (
    <pre className="font-mono text-[11px] text-foreground/70 overflow-auto max-h-48">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

export function AnalysisCollapsibles({ analysis, deviceId, serial, activeSeverities }: Props) {
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

      <Section title="Alertas del portal SDS" color={SEV_COLOR.WARNING} count={0}>
        {deviceId && deviceId !== "manual" ? (
          <SdsAlertsPanel deviceId={deviceId} />
        ) : (
          <p className="font-body text-[13px] text-muted-foreground">
            No disponible para análisis manual.
          </p>
        )}
      </Section>

      <Section title="Incidentes CD" color={SEV_COLOR.INFO} count={0}>
        {deviceId && deviceId !== "manual" ? (
          <CdsIncidentsPanel serial={serial} />
        ) : (
          <p className="font-body text-[13px] text-muted-foreground">
            No disponible para análisis manual.
          </p>
        )}
      </Section>
    </div>
  );
}
