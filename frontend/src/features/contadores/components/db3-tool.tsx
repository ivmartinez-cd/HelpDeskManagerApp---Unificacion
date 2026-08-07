"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Database, Download, FileCode, Loader2 } from "lucide-react";
import { contadoresApi, type Db3ExportResponse } from "../api/contadores-api";

export function Db3Tool() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [fechaMaxima, setFechaMaxima] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Db3ExportResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!files || files.length === 0) {
      toast.error("Por favor seleccioná al menos un archivo SQLite (.db3)");
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }
    if (fechaMaxima) {
      formData.append("fecha_maxima", fechaMaxima);
    }

    setLoading(true);
    setResult(null);

    try {
      const res = await contadoresApi.runDb3Export(formData);
      setResult(res);
      toast.success("Bases de datos DB3 procesadas con éxito");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al procesar archivos DB3";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
          <Database className="h-5 w-5 text-primary" />
          Consolidación de Archivos DB3 a CSV
        </h2>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Archivos SQLite (.db3)
              </label>
              <input
                type="file"
                accept=".db3,.sqlite"
                multiple
                onChange={(e) => setFiles(e.target.files)}
                className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm file:mr-4 file:rounded-lg file:border-0 file:bg-muted file:px-3 file:py-1 file:text-xs file:font-semibold hover:file:bg-muted/80"
                required
              />
              <p className="text-[11px] text-muted-foreground mt-1">
                Podés seleccionar múltiples archivos .db3 simultáneamente.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Fecha Máxima de Lectura (Opcional)
              </label>
              <input
                type="date"
                value={fechaMaxima}
                onChange={(e) => setFechaMaxima(e.target.value)}
                className="w-full rounded-xl border border-input bg-background px-3 flex h-10 items-center text-sm"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-primary-foreground shadow-md shadow-primary/20 hover:bg-primary/90 transition-all disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileCode className="h-4 w-4" />}
            Procesar DB3 a CSV
          </button>
        </form>
      </div>

      {result && (
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-6">
          <h2 className="text-lg font-bold text-foreground">Resultado de Consolidación</h2>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-border bg-muted/20 p-4">
              <p className="text-xs font-medium text-muted-foreground">Total Filas Generadas</p>
              <p className="text-2xl font-black text-foreground mt-1">{result.total_rows}</p>
            </div>
            <div className="rounded-xl border border-border bg-muted/20 p-4">
              <p className="text-xs font-medium text-muted-foreground">Clase 10 (Mono)</p>
              <p className="text-2xl font-black text-foreground mt-1">
                {result.counterclass_10_count}
              </p>
            </div>
            <div className="rounded-xl border border-border bg-muted/20 p-4">
              <p className="text-xs font-medium text-muted-foreground">Clase 20 (Color)</p>
              <p className="text-2xl font-black text-foreground mt-1">
                {result.counterclass_20_count}
              </p>
            </div>
            <div className="rounded-xl border border-border bg-muted/20 p-4">
              <p className="text-xs font-medium text-muted-foreground">Clase 40 (Duplicados)</p>
              <p className="text-2xl font-black text-foreground mt-1">
                {result.counterclass_40_count}
              </p>
            </div>
          </div>

          <div className="pt-2">
            <a
              href={contadoresApi.getOutputUrl(result.csv_filename)}
              download={result.csv_filename}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-xs font-bold text-white shadow-md hover:bg-emerald-700 transition-all"
            >
              <Download className="h-4 w-4" />
              Descargar Archivo CSV Consolidado (.csv)
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
