"use client";

import { ChevronDown, ChevronUp, Loader2, Sparkles } from "lucide-react";
import { useState } from "react";
import type { AnalysisResult, Incident } from "../types/analisis-log-hp";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";

interface Props {
  analysis: AnalysisResult;
  serial: string;
  modelName: string;
  existingDiagnosis?: string | null;
  onDiagnosis?: (diagnosis: string) => void;
}

function buildPayload(
  analysis: AnalysisResult,
  serial: string,
  modelName: string,
): Record<string, unknown> {
  return {
    serial,
    model: modelName,
    global_severity: analysis.global_severity,
    events_count: analysis.events_count,
    incidents: analysis.incidents.map((i: Incident) => ({
      code: i.code,
      classification: i.classification,
      severity: i.severity,
      occurrences: i.occurrences,
      description: i.code_description ?? null,
    })),
  };
}

export function AiDiagnosisCard({ analysis, serial, modelName, existingDiagnosis, onDiagnosis }: Props) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [diagnosis, setDiagnosis] = useState<string | null>(existingDiagnosis ?? null);

  async function handleDiagnose() {
    setError(null);
    setLoading(true);
    try {
      const payload = buildPayload(analysis, serial, modelName);
      const result = await analisisLogHpApi.aiDiagnose(payload);
      setDiagnosis(result.diagnosis);
      setOpen(true);
      onDiagnosis?.(result.diagnosis);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al conectar con el servicio de IA";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-[12px] border border-brand-orange/20 bg-card p-4 flex flex-col gap-2">
      <button
        type="button"
        onClick={() => (diagnosis ? setOpen((o) => !o) : handleDiagnose())}
        className="flex items-center gap-2 text-left w-full"
        disabled={loading}
      >
        <Sparkles className="h-4 w-4 text-brand-orange flex-none" />
        <span className="font-heading text-[13px] font-bold text-foreground flex-1">
          Diagnóstico con IA{" "}
          <span className="font-body text-[11px] font-normal text-brand-orange">(Recomendado)</span>
        </span>
        {loading ? (
          <Loader2 className="h-4 w-4 text-muted-foreground animate-spin flex-none" />
        ) : diagnosis ? (
          open ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground flex-none" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground flex-none" />
          )
        ) : null}
      </button>

      {!diagnosis && !loading && (
        <p className="font-body text-[12px] text-muted-foreground ml-6">
          Analizá este reporte con IA para obtener un diagnóstico detallado y recomendaciones de acción.
        </p>
      )}

      {error && (
        <p className="font-body text-[12px] text-destructive ml-6">{error}</p>
      )}

      {diagnosis && open && (
        <div className="ml-6 mt-1 font-body text-[13px] text-foreground/90 leading-relaxed whitespace-pre-wrap border-l-2 border-brand-orange/30 pl-3">
          {diagnosis}
        </div>
      )}

      {diagnosis && !open && (
        <p className="ml-6 font-body text-[12px] text-muted-foreground">
          Diagnóstico listo. Hacé clic para expandir.
        </p>
      )}
    </div>
  );
}
