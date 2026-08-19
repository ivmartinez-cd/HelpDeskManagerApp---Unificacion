import { forwardRef } from "react";
import type { AnalysisResult } from "../../types/analisis-log-hp";
import { ReportAiSummary } from "./report-ai-summary";
import { ReportHeader } from "./report-header";
import { ReportIncidentsTable } from "./report-incidents-table";
import { ReportKpis } from "./report-kpis";

interface Props {
  serial: string;
  modelName: string;
  analysis: AnalysisResult;
  aiSummary: string | null;
  generatedAtIso: string;
}

export const ExecutivePrintReport = forwardRef<HTMLDivElement, Props>(function ExecutivePrintReport(
  { serial, modelName, analysis, aiSummary, generatedAtIso },
  ref,
) {
  return (
    <div
      ref={ref}
      style={{
        width: "210mm", minHeight: "297mm", padding: "16mm",
        backgroundColor: "#fff", color: "#111", boxSizing: "border-box",
        fontFamily: "Arial, Helvetica, sans-serif",
      }}
    >
      <ReportHeader
        serial={serial}
        modelName={modelName}
        globalSeverity={analysis.global_severity}
        generatedAtIso={generatedAtIso}
      />
      <ReportKpis analysis={analysis} />
      <ReportAiSummary summary={aiSummary} />
      <ReportIncidentsTable analysis={analysis} />
    </div>
  );
});
