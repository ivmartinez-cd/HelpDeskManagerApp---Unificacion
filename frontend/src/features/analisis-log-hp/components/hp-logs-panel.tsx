"use client";

import { ArrowLeft, Loader2, RefreshCw, Save } from "lucide-react";
import { useState } from "react";
import type { AnalysisResult, SdsExtractResult, Severity } from "../types/analisis-log-hp";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";
import { AiDiagnosisCard } from "./ai-diagnosis-card";
import { AnalysisCollapsibles } from "./analysis-collapsibles";
import { ErrorCharts } from "./error-charts";
import { ErrorHeatmap } from "./error-heatmap";
import { ErrorTimeline } from "./error-timeline";
import { KpiCards } from "./kpi-cards";
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
  const [activeSeverities, setActiveSeverities] = useState<Set<Severity>>(new Set());
  const [diagnosis, setDiagnosis] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

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
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={onBack}
            title="Volver"
            className="flex h-9 w-9 items-center justify-center rounded-[8px] border border-border bg-card text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          {deviceId !== "manual" && (
            <>
              <button
                type="button"
                onClick={handleEws}
                className="rounded-[8px] border border-border bg-card px-3 py-2 font-body text-[12px] text-muted-foreground hover:text-foreground transition-colors"
              >
                EWS Remoto
              </button>
              <button
                type="button"
                onClick={handleRefresh}
                disabled={refreshing}
                className="flex items-center gap-1.5 rounded-[8px] border border-border bg-card px-3 py-2 font-body text-[12px] text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
              >
                {refreshing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
                Actualizar caché HP
              </button>
            </>
          )}
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1.5 rounded-[8px] border border-border bg-card px-3 py-2 font-body text-[12px] text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
          >
            {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
            Guardar
          </button>
        </div>
      </div>

      {saveMsg && (
        <div className="rounded-[8px] border border-border bg-card px-3 py-2 font-body text-[12px] text-muted-foreground">
          {saveMsg}
        </div>
      )}

      {/* KPIs */}
      <KpiCards analysis={analysis} activeSeverities={activeSeverities} />

      {/* Filtro de severidad */}
      <SeverityFilter active={activeSeverities} onChange={setActiveSeverities} />

      {/* Gráficos */}
      <ErrorCharts analysis={analysis} activeSeverities={activeSeverities} />

      {/* Heatmap */}
      <ErrorHeatmap analysis={analysis} dateRange={dateRangeLabel(analysis.events)} />

      {/* Timeline */}
      <ErrorTimeline analysis={analysis} activeSeverities={activeSeverities} />

      {/* IA */}
      <AiDiagnosisCard
        analysis={analysis}
        serial={serial}
        modelName={modelName}
        onDiagnosis={setDiagnosis}
      />

      {/* Collapsibles detallados */}
      <AnalysisCollapsibles
        analysis={analysis}
        deviceId={deviceId !== "manual" ? deviceId : null}
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
    </div>
  );
}
