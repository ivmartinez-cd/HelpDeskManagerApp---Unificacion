import type { AnalysisResult } from "../../types/analisis-log-hp";
import { computeErrorRate, lastCriticalIncident } from "../../utils/analysis-utils";

function Kpi({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div style={{ flex: 1, border: "1px solid #ddd", borderRadius: 8, padding: 10 }}>
      <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", color: "#888" }}>
        {label}
      </div>
      <div style={{ fontSize: 18, fontWeight: 800, color: "#111", marginTop: 2 }}>{value}</div>
      {sub && <div style={{ fontSize: 10, color: "#666", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

export function ReportKpis({ analysis }: { analysis: AnalysisResult }) {
  const last = lastCriticalIncident(analysis.incidents);
  const errorRate = computeErrorRate(analysis.events);
  const errorCount = analysis.incidents.filter((i) => i.severity === "ERROR").length;

  return (
    <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
      <Kpi label="Último error crítico" value={last?.code ?? "—"} sub={last?.code_description ?? "Sin errores en el período"} />
      <Kpi label="Errores críticos" value={String(errorCount)} />
      <Kpi label="Incidencias activas" value={String(analysis.incidents.length)} sub="en el período" />
      <Kpi label="Tasa de errores" value={errorRate.label} sub={errorRate.sub} />
    </div>
  );
}
