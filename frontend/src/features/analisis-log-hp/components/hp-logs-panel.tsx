"use client";

import { useMemo, useState } from "react";
import { ApiError } from "@/services/http-client";
import { useSession } from "@/services/session-provider";
import type { AnalysisResult, SdsExtractResult, Severity } from "../types/analisis-log-hp";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";
import { useExportPdf } from "../hooks/use-export-pdf";
import {
  type DateFilter,
  filterEventsByDateFilter,
  filterIncidentsByDateFilter,
} from "../utils/date-filter";
import { AiDiagnosisCard, buildPayload } from "./ai-diagnosis-card";
import { AnalysisCollapsibles } from "./analysis-collapsibles";
import { CpmdUploadModal } from "./cpmd-upload-modal";
import { ErrorCharts } from "./error-charts";
import { ErrorHeatmap } from "./error-heatmap";
import { ErrorTimeline } from "./error-timeline";
import { ExecutivePrintReport } from "./executive-print-report";
import { KpiCards } from "./kpi-cards";
import { PanelToolbar } from "./panel-toolbar";
import { SeverityFilter } from "./severity-filter";

interface Props {
  serial: string;
  modelName: string;
  deviceId: string;
  sdsResult: SdsExtractResult;
  analysis: AnalysisResult;
  onBack: () => void;
  onAnalysisUpdate?: (a: AnalysisResult, s: SdsExtractResult) => void;
}

function dateRangeLabel(events: AnalysisResult["events"]): string {
  if (!events.length) return "Sin eventos";
  const dates = events.map((e) => new Date(e.timestamp));
  const min = new Date(Math.min(...dates.map((d) => d.getTime())));
  const max = new Date(Math.max(...dates.map((d) => d.getTime())));
  const fmt = (d: Date) =>
    d.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "2-digit" });
  return `${fmt(min)} → ${fmt(max)}`;
}

export function HpLogsPanel({
  serial,
  modelName,
  deviceId,
  sdsResult,
  analysis,
  onBack,
  onAnalysisUpdate,
}: Props) {
  // Guardar análisis y subir manuales CPMD son analisis-log-hp.manage — los botones
  // se ocultan/redirigen, el backend igual corta (ver well_known_permissions.py).
  const { can } = useSession();
  const puedeEditar = can("analisis-log-hp", "manage");
  const [activeSeverities, setActiveSeverities] = useState<Set<Severity>>(new Set());
  const [dateFilter, setDateFilter] = useState<DateFilter>("all");
  const [diagnosis, setDiagnosis] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [cpmdModalOpen, setCpmdModalOpen] = useState(false);
  const [pdfSummary, setPdfSummary] = useState<string | null>(null);
  const [pdfGeneratedAt, setPdfGeneratedAt] = useState<string>("");
  const { exportingPdf, handleExportPdf, printReportRef } = useExportPdf(serial);

  const scopedAnalysis: AnalysisResult = useMemo(() => {
    const events = filterEventsByDateFilter(analysis.events, dateFilter);
    const incidents = filterIncidentsByDateFilter(analysis.incidents, dateFilter);
    return { ...analysis, events, incidents, events_count: events.length };
  }, [analysis, dateFilter]);

  async function handleSave() {
    setSaving(true);
    setSaveMsg(null);
    try {
      const name = `${serial} — ${new Date().toLocaleDateString("es-AR")}`;
      await analisisLogHpApi.createSavedAnalysis({
        name,
        equipment_identifier: `${modelName} · S/N ${serial}`,
        incidents: analysis.incidents,
        global_severity: analysis.global_severity,
        ai_diagnosis: diagnosis,
      });
      setSaveMsg("Guardado correctamente.");
    } catch {
      setSaveMsg("Error al guardar.");
    } finally {
      setSaving(false);
    }
  }

  async function handleRefresh() {
    if (deviceId === "manual") return;
    setRefreshing(true);
    try {
      await analisisLogHpApi.refreshCache(deviceId);
      const newSds = await analisisLogHpApi.extractLogs(serial, 30);
      const newAnalysis = await analisisLogHpApi.previewAnalysis(newSds.tsv);
      onAnalysisUpdate?.(newAnalysis, newSds);
    } catch {
      /* silencioso — no hay UI de error en la botonera */
    } finally {
      setRefreshing(false);
    }
  }

  async function handleCpmd() {
    try {
      const { url } = await analisisLogHpApi.getCpmdPdfUrl(modelName);
      window.open(url, "_blank");
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 404) {
        if (puedeEditar) setCpmdModalOpen(true);
        else alert("No hay manual CPMD cargado para este modelo. Pedile a un admin que lo suba.");
      }
    }
  }

  async function handleExportPdfClick() {
    setPdfGeneratedAt(new Date().toISOString());
    try {
      const payload = buildPayload(scopedAnalysis, serial, modelName);
      const result = await analisisLogHpApi.generatePdfSummary(payload);
      setPdfSummary(result.diagnosis);
    } catch {
      setPdfSummary(null); // sin resumen de IA, el reporte se exporta igual
    }
    // Esperar a que React commitee `pdfSummary` en el DOM antes de leer
    // `printReportRef.current.outerHTML` (si no, el hook lee el HTML viejo).
    await new Promise<void>((resolve) =>
      requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
    );
    await handleExportPdf();
  }

  async function handleEws() {
    if (deviceId === "manual") return;
    const { url } = await analisisLogHpApi.getRemoteEws(deviceId);
    if (url) window.open(url, "_blank");
    else alert("EWS Remoto no disponible para este equipo.");
  }

  return (
    <div className="flex flex-col gap-5 px-6 py-6 pb-10">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-heading text-[20px] font-extrabold text-foreground">
            Panel de errores
          </h1>
          <p className="font-body text-[13px] text-muted-foreground mt-0.5">
            {modelName} · S/N {serial}
          </p>
        </div>
        <PanelToolbar
          deviceId={deviceId}
          dateFilter={dateFilter}
          onDateFilterChange={setDateFilter}
          onBack={onBack}
          onEws={handleEws}
          onRefresh={handleRefresh}
          refreshing={refreshing}
          onCpmd={handleCpmd}
          onExportPdf={handleExportPdfClick}
          exportingPdf={exportingPdf}
          onSave={handleSave}
          saving={saving}
          canSave={puedeEditar}
        />
      </div>

      {saveMsg && (
        <div className="rounded-[8px] border border-border bg-card px-3 py-2 font-body text-[12px] text-muted-foreground">
          {saveMsg}
        </div>
      )}

      {/* KPIs */}
      <KpiCards analysis={scopedAnalysis} activeSeverities={activeSeverities} />

      {/* Filtro de severidad */}
      <SeverityFilter active={activeSeverities} onChange={setActiveSeverities} />

      {/* Gráficos */}
      <ErrorCharts analysis={scopedAnalysis} activeSeverities={activeSeverities} />

      {/* Heatmap */}
      <ErrorHeatmap analysis={scopedAnalysis} dateRange={dateRangeLabel(scopedAnalysis.events)} />

      {/* Timeline */}
      <ErrorTimeline analysis={scopedAnalysis} activeSeverities={activeSeverities} />

      {/* IA */}
      <AiDiagnosisCard
        analysis={scopedAnalysis}
        serial={serial}
        modelName={modelName}
        onDiagnosis={setDiagnosis}
      />

      {/* Collapsibles detallados */}
      <AnalysisCollapsibles
        analysis={scopedAnalysis}
        deviceId={deviceId !== "manual" ? deviceId : null}
        serial={serial}
        activeSeverities={activeSeverities}
      />

      {/* Código de nuevos errores sin catalogar */}
      {analysis.codes_new.length > 0 && (
        <div className="rounded-[12px] border border-warning/20 bg-warning/5 px-4 py-3">
          <p className="font-body text-[12px] text-warning font-semibold">
            {analysis.codes_new.length} código(s) sin catalogar:{" "}
            {analysis.codes_new.join(", ")}
          </p>
        </div>
      )}

      {cpmdModalOpen && (
        <CpmdUploadModal
          modelName={modelName}
          onClose={() => setCpmdModalOpen(false)}
          onUploaded={(url) => { setCpmdModalOpen(false); window.open(url, "_blank"); }}
        />
      )}

      {/* Reporte oculto — solo se lee su outerHTML para armar el PDF (useExportPdf) */}
      <div aria-hidden="true" style={{ position: "fixed", top: -99999, left: -99999 }}>
        <ExecutivePrintReport
          ref={printReportRef}
          serial={serial}
          modelName={modelName}
          analysis={scopedAnalysis}
          aiSummary={pdfSummary}
          generatedAtIso={pdfGeneratedAt || new Date().toISOString()}
        />
      </div>
    </div>
  );
}
