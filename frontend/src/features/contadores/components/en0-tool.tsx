"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Download, FileSpreadsheet, Loader2 } from "lucide-react";
import { contadoresApi, type EstimationZeroResponse } from "../api/contadores-api";

export function En0Tool() {
  const [file, setFile] = useState<File | null>(null);
  const [cliente, setCliente] = useState("");
  const [fecha, setFecha] = useState(new Date().toISOString().split("T")[0]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EstimationZeroResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !cliente || !fecha) {
      toast.error("Por favor completá todos los campos");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("cliente", cliente);
    formData.append("fecha", fecha);

    setLoading(true);
    setResult(null);

    try {
      const res = await contadoresApi.runEstimationZero(formData);
      setResult(res);
      toast.success("Planilla de Estimación en 0 procesada con éxito");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al procesar la planilla";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
          <FileSpreadsheet className="h-5 w-5 text-primary" />
          Procesamiento de Estimación en 0 (Falta Contador)
        </h2>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid gap-5 md:grid-cols-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Archivo CSV / Falta Contador
              </label>
              <input
                type="file"
                accept=".csv,.txt"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm file:mr-4 file:rounded-lg file:border-0 file:bg-muted file:px-3 file:py-1 file:text-xs file:font-semibold hover:file:bg-muted/80"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Nombre del Cliente
              </label>
              <input
                type="text"
                value={cliente}
                onChange={(e) => setCliente(e.target.value)}
                placeholder="Ej: BANCO DE CORRIENTES"
                className="w-full rounded-xl border border-input bg-background px-3 flex h-10 items-center text-sm"
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
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-primary-foreground shadow-md shadow-primary/20 hover:bg-primary/90 transition-all disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheet className="h-4 w-4" />}
            Procesar Estimación en 0
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

          <div>
            <a
              href={contadoresApi.getOutputUrl(result.csv_filename)}
              download={result.csv_filename}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-xs font-bold text-white shadow-md hover:bg-emerald-700 transition-all"
            >
              <Download className="h-4 w-4" />
              Descargar Archivo CSV Resultado (.csv)
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
