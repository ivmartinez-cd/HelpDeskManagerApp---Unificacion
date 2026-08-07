"use client";

import { useState } from "react";
import { toast } from "sonner";
import {
  BarChart3,
  ChevronDown,
  ChevronUp,
  Download,
  FileSpreadsheet,
  Loader2,
  Sparkles,
} from "lucide-react";
import { contadoresApi, type ProyeccionResponse } from "../api/contadores-api";

export function ProyeccionTool() {
  const [file, setFile] = useState<File | null>(null);
  const [fechaToma, setFechaToma] = useState<string>(
    new Date().toISOString().split("T")[0],
  );
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ProyeccionResponse | null>(null);

  // Parámetros avanzados
  const [toleranciaDias, setToleranciaDias] = useState(2);
  const [minDiasIntervalo, setMinDiasIntervalo] = useState(1);
  const [ventanaRecienteDias, setVentanaRecienteDias] = useState(365);
  const [umbralMinimoConsumo, setUmbralMinimoConsumo] = useState(0.2);
  const [maxAntiguedadLecturaDias, setMaxAntiguedadLecturaDias] = useState(365);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      toast.error("Por favor seleccioná un archivo Excel (.xlsx)");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("fecha_toma", fechaToma);
    formData.append("tolerancia_dias", String(toleranciaDias));
    formData.append("min_dias_intervalo", String(minDiasIntervalo));
    formData.append("ventana_reciente_dias", String(ventanaRecienteDias));
    formData.append("umbral_minimo_consumo", String(umbralMinimoConsumo));
    formData.append("max_antiguedad_lectura_dias", String(maxAntiguedadLecturaDias));

    setLoading(true);
    setResult(null);

    try {
      const res = await contadoresApi.runProyeccion(formData);
      setResult(res);
      toast.success("Proyección ejecutada correctamente");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al procesar la proyección";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Archivo Excel de Contadores (.xlsx)
              </label>
              <input
                type="file"
                accept=".xlsx"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm file:mr-4 file:rounded-lg file:border-0 file:bg-muted file:px-3 file:py-1 file:text-xs file:font-semibold hover:file:bg-muted/80"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Fecha de Toma para Proyección
              </label>
              <input
                type="date"
                value={fechaToma}
                onChange={(e) => setFechaToma(e.target.value)}
                className="w-full rounded-xl border border-input bg-background px-3 flex h-10 items-center text-sm"
                required
              />
            </div>
          </div>

          {/* Configuración avanzada acordeón */}
          <div className="rounded-xl border border-border/70 bg-muted/30 p-4">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex w-full items-center justify-between text-xs font-bold uppercase tracking-wider text-foreground"
            >
              <span>Parámetros del Algoritmo de Proyección</span>
              {showAdvanced ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>

            {showAdvanced && (
              <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 pt-3 border-t border-border/50">
                <div>
                  <label className="block text-[11px] font-medium text-muted-foreground mb-1">
                    Tolerancia de días (Días)
                  </label>
                  <input
                    type="number"
                    value={toleranciaDias}
                    onChange={(e) => setToleranciaDias(Number(e.target.value))}
                    className="w-full rounded-lg border border-input bg-background px-3 py-1.5 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-muted-foreground mb-1">
                    Mínimo días intervalo
                  </label>
                  <input
                    type="number"
                    value={minDiasIntervalo}
                    onChange={(e) => setMinDiasIntervalo(Number(e.target.value))}
                    className="w-full rounded-lg border border-input bg-background px-3 py-1.5 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-muted-foreground mb-1">
                    Ventana reciente (Días)
                  </label>
                  <input
                    type="number"
                    value={ventanaRecienteDias}
                    onChange={(e) => setVentanaRecienteDias(Number(e.target.value))}
                    className="w-full rounded-lg border border-input bg-background px-3 py-1.5 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-muted-foreground mb-1">
                    Umbral mínimo consumo (/día)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={umbralMinimoConsumo}
                    onChange={(e) => setUmbralMinimoConsumo(Number(e.target.value))}
                    className="w-full rounded-lg border border-input bg-background px-3 py-1.5 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-muted-foreground mb-1">
                    Máx. antigüedad lectura (Días)
                  </label>
                  <input
                    type="number"
                    value={maxAntiguedadLecturaDias}
                    onChange={(e) => setMaxAntiguedadLecturaDias(Number(e.target.value))}
                    className="w-full rounded-lg border border-input bg-background px-3 py-1.5 text-xs"
                  />
                </div>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-primary-foreground shadow-md shadow-primary/20 hover:bg-primary/90 transition-all disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            Ejecutar Proyección
          </button>
        </form>
      </div>

      {/* Resultados */}
      {result && (
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-6">
          <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            Resultados de Proyección
          </h2>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-border/60 bg-muted/20 p-4">
              <p className="text-xs font-medium text-muted-foreground">Total Series</p>
              <p className="text-2xl font-black text-foreground mt-1">{result.total_series}</p>
            </div>
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
              <p className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
                Proyectadas
              </p>
              <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">
                {result.series_proyectadas}
              </p>
            </div>
            <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">
              <p className="text-xs font-medium text-blue-600 dark:text-blue-400">Reales</p>
              <p className="text-2xl font-black text-blue-600 dark:text-blue-400 mt-1">
                {result.series_reales}
              </p>
            </div>
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
              <p className="text-xs font-medium text-amber-600 dark:text-amber-400">
                Sin Datos / Insuficiente
              </p>
              <p className="text-2xl font-black text-amber-600 dark:text-amber-400 mt-1">
                {result.series_sin_datos}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-3 pt-2 border-t border-border">
            <a
              href={contadoresApi.getOutputUrl(result.xlsx_filename)}
              download={result.xlsx_filename}
              className="flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white shadow-md hover:bg-emerald-700 transition-all"
            >
              <FileSpreadsheet className="h-4 w-4" />
              Descargar Reporte Excel Completo (.xlsx)
            </a>
            <a
              href={contadoresApi.getOutputUrl(result.csv_filename)}
              download={result.csv_filename}
              className="flex items-center gap-2 rounded-xl border border-border bg-background px-4 py-2 text-xs font-bold text-foreground shadow-sm hover:bg-muted transition-all"
            >
              <Download className="h-4 w-4" />
              Descargar CSV para SiGes (.csv)
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
