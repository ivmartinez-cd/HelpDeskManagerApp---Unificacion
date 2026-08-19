import type { AnalysisResult, Severity } from "../types/analisis-log-hp";
import {
  SEV_COLOR,
  computeErrorRate,
  filterEventsBySeverity,
  filterIncidentsBySeverity,
  lastCriticalIncident,
  normSev,
  relativeTime,
} from "../utils/analysis-utils";

interface Props {
  analysis: AnalysisResult;
  activeSeverities: Set<Severity>;
}

export function KpiCards({ analysis, activeSeverities }: Props) {
  const visible = filterIncidentsBySeverity(analysis.incidents, activeSeverities);
  const last = lastCriticalIncident(visible);
  const visibleEvents = filterEventsBySeverity(analysis.events, activeSeverities);
  const errorRate = computeErrorRate(visibleEvents);

  const errorCount = visible.filter((i) => normSev(i.severity) === "ERROR").length;
  const warnCount = visible.filter((i) => normSev(i.severity) === "WARNING").length;
  const infoCount = visible.filter((i) => normSev(i.severity) === "INFO").length;

  return (
    <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
      {/* KPI 1 — Último error crítico */}
      <div
        className="rounded-[12px] border bg-card p-4 flex flex-col gap-1"
        style={{ borderColor: last ? `${SEV_COLOR["ERROR"]}40` : undefined }}
      >
        <span className="font-body text-[10px] font-bold uppercase tracking-[.05em] text-muted-foreground">
          Último error crítico
        </span>
        {last ? (
          <>
            <div
              className="font-heading text-[22px] font-extrabold leading-tight"
              style={{ color: SEV_COLOR["ERROR"] }}
            >
              {last.code}
            </div>
            <div className="font-body text-xs text-muted-foreground">
              {relativeTime(last.end_time)} ·{" "}
              {last.code_description
                ? last.code_description.slice(0, 32)
                : "—"}
            </div>
          </>
        ) : (
          <>
            <div className="font-heading text-[22px] font-extrabold leading-tight text-muted-foreground">—</div>
            <div className="font-body text-xs text-muted-foreground">Sin errores en el período</div>
          </>
        )}
      </div>

      {/* KPI 2 — Errores críticos */}
      <div className="rounded-[12px] border border-border bg-card p-4 flex flex-col gap-1">
        <span className="font-body text-[10px] font-bold uppercase tracking-[.05em] text-muted-foreground">
          Errores críticos
        </span>
        <div
          className="font-heading text-[22px] font-extrabold leading-tight"
          style={{ color: errorCount > 0 ? SEV_COLOR["ERROR"] : undefined }}
        >
          {errorCount}
        </div>
        <div className="font-body text-xs text-muted-foreground">
          {warnCount > 0 && `${warnCount} advert.`}
          {warnCount > 0 && infoCount > 0 && " · "}
          {infoCount > 0 && `${infoCount} info`}
          {warnCount === 0 && infoCount === 0 && "Sin advertencias"}
        </div>
      </div>

      {/* KPI 3 — Incidencias activas */}
      <div className="rounded-[12px] border border-border bg-card p-4 flex flex-col gap-1">
        <span className="font-body text-[10px] font-bold uppercase tracking-[.05em] text-muted-foreground">
          Incidencias activas
        </span>
        <div className="font-heading text-[22px] font-extrabold leading-tight text-brand-orange">
          {visible.length}
        </div>
        <div className="font-body text-xs text-muted-foreground">en el período</div>
      </div>

      {/* KPI 4 — Tasa de errores */}
      <div className="rounded-[12px] border border-border bg-card p-4 flex flex-col gap-1">
        <span className="font-body text-[10px] font-bold uppercase tracking-[.05em] text-muted-foreground">
          Tasa de errores
        </span>
        <div
          className={`font-heading text-[22px] font-extrabold leading-tight ${
            errorRate.labelColor ? "text-success" : "text-brand-orange"
          }`}
        >
          {errorRate.label}
        </div>
        <div className="font-body text-xs text-muted-foreground">
          {errorRate.sub}
          {errorRate.pagesInPeriod > 0 && (
            <>
              <br />
              {`En periodo: ${errorRate.pagesInPeriod.toLocaleString("es-AR")} pág.`}
            </>
          )}
          {errorRate.totalCounter > 0 && (
            <>
              <br />
              {`Contador total: ${errorRate.totalCounter.toLocaleString("es-AR")} pág.`}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
