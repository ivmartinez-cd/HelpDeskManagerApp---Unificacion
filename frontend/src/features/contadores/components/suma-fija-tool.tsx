"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Download, FileSpreadsheetIcon, Loader2 } from "lucide-react";
import { contadoresApi, type FixedSumResponse } from "../api/contadores-api";

export function SumaFijaTool() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [fecha, setFecha] = useState(new Date().toISOString().split("T")[0]);
  const [hojas, setHojas] = useState<number | "">(500);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FixedSumResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!files || files.length === 0 || !fecha || hojas === "") {
      toast.error("Por favor completá todos los campos requeridos");
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }
    formData.append("fecha", fecha);
    formData.append("hojas", String(hojas));

    setLoading(true);
    setResult(null);

    try {
      const res = await contadoresApi.runFixedSum(formData);
      setResult(res);
      toast.success("Archivos de Suma Fija procesados con éxito");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al procesar la Suma Fija";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
          <FileSpreadsheetIcon className="h-5 w-5 text-primary" />
          Procesamiento de Suma Fija en Excel
        </h2>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid gap-5 md:grid-cols-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Archivos Excel (.xlsx)
              </label>
              <input
                type="file"
                accept=".xlsx"
                multiple
                onChange={(e) => setFiles(e.target.files)}
                className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm file:mr-4 file:rounded-lg file:border-0 file:bg-muted file:px-3 file:py-1 file:text-xs file:font-semibold hover:file:bg-muted/80"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Fecha de Lectura
              </label>
              <input
                type="date"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                className="w-full rounded-xl border border-input bg-background px-3 flex h-10 items-center text-sm"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Hojas a Sumar
              </label>
              <input
                type="number"
                min="1"
                value={hojas}
                onChange={(e) => setHojas(e.target.value === "" ? "" : Number(e.target.value))}
                placeholder="Ej: 500"
                className="w-full rounded-xl border border-input bg-background px-3 flex h-10 items-center text-sm"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-primary-foreground shadow-md shadow-primary/20 hover:bg-primary/90 transition-all disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheetIcon className="h-4 w-4" />}
            Procesar Suma Fija
          </button>
        </form>
      </div>

      {result && (
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-6">
          <h2 className="text-lg font-bold text-foreground">Resultado del Procesamiento</h2>

          <div className="rounded-xl border border-border bg-muted/20 p-4 max-w-xs">
            <p className="text-xs font-medium text-muted-foreground">Total Filas Generadas</p>
            <p className="text-2xl font-black text-foreground mt-1">{result.total_rows}</p>
          </div>

          <div className="space-y-3">
            <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Archivos CSV Generados ({result.csv_filenames.length}):
            </p>
            <div className="flex flex-wrap gap-3">
              {result.csv_filenames.map((fname) => (
                <a
                  key={fname}
                  href={contadoresApi.getOutputUrl(fname)}
                  download={fname}
                  className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white shadow-md hover:bg-emerald-700 transition-all"
                >
                  <Download className="h-4 w-4" />
                  Descargar {fname}
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
