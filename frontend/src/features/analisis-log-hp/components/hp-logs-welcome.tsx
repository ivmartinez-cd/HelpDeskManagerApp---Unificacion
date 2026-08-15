"use client";

import { AlertCircle, FileText, HelpCircle, Loader2, Search } from "lucide-react";
import { useState } from "react";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";
import type { AnalysisResult, SdsExtractResult } from "../types/analisis-log-hp";

interface Props {
  onResult: (
    serial: string,
    modelName: string,
    deviceId: string,
    sdsResult: SdsExtractResult,
    analysis: AnalysisResult,
  ) => void;
}

const MODE_OPTIONS = [
  { value: "serie", label: "Buscar por Serie" },
  { value: "manual", label: "Análisis Manual" },
];

export function HpLogsWelcome({ onResult }: Props) {
  const [mode, setMode] = useState<"serie" | "manual">("serie");
  const [serial, setSerial] = useState("");
  const [tsv, setTsv] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    setError(null);
    if (mode === "serie") {
      if (!serial.trim()) return;
      setLoading(true);
      try {
        const sdsResult = await analisisLogHpApi.extractLogs(serial.trim());
        const analysis = await analisisLogHpApi.previewAnalysis(sdsResult.tsv);
        onResult(serial.trim(), sdsResult.model_name, sdsResult.device_id, sdsResult, analysis);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Error al conectar con HP SDS";
        setError(msg);
      } finally {
        setLoading(false);
      }
    } else {
      if (!tsv.trim()) return;
      setLoading(true);
      try {
        const analysis = await analisisLogHpApi.previewAnalysis(tsv.trim());
        const fake: SdsExtractResult = {
          device_id: "manual",
          model_name: "Manual",
          tsv: tsv.trim(),
          help_urls_updated: 0,
        };
        onResult("MANUAL", "Análisis Manual", "manual", fake, analysis);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Error al analizar los logs";
        setError(msg);
      } finally {
        setLoading(false);
      }
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] px-4 py-12">
      <div className="w-full max-w-xl flex flex-col items-center gap-6">
        {/* Título */}
        <div className="text-center">
          <h1 className="font-heading text-[36px] font-extrabold leading-tight">
            <span className="text-foreground">HP Logs</span>{" "}
            <span className="text-brand-orange">ANALYZER</span>
          </h1>
          <p className="mt-2 font-body text-[13px] text-muted-foreground max-w-sm mx-auto">
            Análisis técnico avanzado de logs HP con detección inteligente de errores
            y estado de hardware en tiempo real.
          </p>
        </div>

        {/* Toggle de modo */}
        <SegmentedControl
          options={MODE_OPTIONS}
          value={mode}
          onChange={(v) => { setMode(v as "serie" | "manual"); setError(null); }}
        />

        {/* Input */}
        {mode === "serie" ? (
          <div className="w-full flex gap-2">
            <input
              type="text"
              value={serial}
              onChange={(e) => setSerial(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleAnalyze(); }}
              placeholder="Ingrese Serie de Impresora (ej: MXBCN...)"
              className="flex-1 rounded-[10px] border border-border bg-card px-4 py-3 font-body text-sm text-foreground placeholder:text-muted-foreground focus:border-brand-orange/60 focus:outline-none"
              disabled={loading}
            />
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={loading || !serial.trim()}
              className="flex items-center gap-2 rounded-[10px] bg-brand-orange px-5 py-3 font-body text-sm font-bold text-white hover:bg-brand-orange/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Analizar
            </button>
            <button
              type="button"
              title="El número de serie se encuentra en la etiqueta del equipo o en la pantalla de configuración HP."
              className="flex h-[46px] w-[46px] items-center justify-center rounded-[10px] border border-border bg-card text-muted-foreground hover:text-foreground transition-colors"
            >
              <HelpCircle className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="w-full flex flex-col gap-3">
            <textarea
              value={tsv}
              onChange={(e) => setTsv(e.target.value)}
              placeholder={"Pegá los logs HP aquí para analizar...\n\n(formato TSV exportado desde HP SDS)"}
              rows={8}
              className="w-full rounded-[10px] border border-border bg-card px-4 py-3 font-mono text-xs text-foreground placeholder:text-muted-foreground focus:border-brand-orange/60 focus:outline-none resize-none"
              disabled={loading}
            />
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={loading || !tsv.trim()}
              className="flex items-center justify-center gap-2 rounded-[10px] bg-brand-orange px-5 py-3 font-body text-sm font-bold text-white hover:bg-brand-orange/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              🚀 Iniciar Análisis
            </button>
            <p className="text-center font-body text-[11px] text-muted-foreground">
              ⚠️ El análisis de logs extensos puede tardar algunos segundos.
            </p>
          </div>
        )}

        {/* Hint */}
        {mode === "serie" && (
          <p className="font-body text-[12px] text-muted-foreground">
            💡 Pegá un número de serie para un diagnóstico instantáneo vía HP SDS Portal.
          </p>
        )}

        {/* Error */}
        {error && (
          <div className="w-full flex items-start gap-2.5 rounded-[10px] border border-destructive/30 bg-destructive/10 px-4 py-3 text-destructive">
            <AlertCircle className="h-4 w-4 mt-0.5 flex-none" />
            <span className="font-body text-[13px]">{error}</span>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && (
          <div className="w-full rounded-[12px] border border-dashed border-border bg-card/50 px-8 py-10 flex flex-col items-center gap-3 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-[12px] bg-muted">
              <FileText className="h-6 w-6 text-muted-foreground" />
            </div>
            <p className="font-heading text-[15px] font-bold text-foreground">Sin diagnóstico todavía</p>
            <p className="font-body text-[13px] text-muted-foreground">
              Ingresá un número de serie para traer los últimos logs desde HP SDS.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
