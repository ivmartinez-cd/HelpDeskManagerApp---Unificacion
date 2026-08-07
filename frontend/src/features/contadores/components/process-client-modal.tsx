"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Download, Loader2, X } from "lucide-react";
import { contadoresApi } from "../api/contadores-api";

interface Props {
  isOpen: boolean;
  type: "ftp" | "sds" | "ers";
  targetId: string;
  targetName: string;
  onClose: () => void;
}

export function ProcessClientModal({
  isOpen,
  type,
  targetId,
  targetName,
  onClose,
}: Props) {
  const [fechaMaxima, setFechaMaxima] = useState(
    new Date().toISOString().split("T")[0],
  );
  const [loading, setLoading] = useState(false);
  const [generatedCsv, setGeneratedCsv] = useState<string | null>(null);

  if (!isOpen) return null;

  const titleMap = {
    ftp: "Descargar y Procesar DB3 de Cliente FTP",
    sds: "Descargar Contadores HP SDS",
    ers: "Descargar Telemetría Epson ERS",
  };

  const handleProcess = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setGeneratedCsv(null);

    try {
      if (type === "ftp") {
        const res = await contadoresApi.processFtpClient(targetId, fechaMaxima);
        setGeneratedCsv(res.csv_filename);
        toast.success(`DB3 procesada exitosamente (${res.total_rows} filas)`);
      } else if (type === "sds") {
        const res = await contadoresApi.processSds({
          customer_id: targetId,
          customer_name: targetName,
          fecha_maxima: fechaMaxima,
        });
        setGeneratedCsv(res.csv_filename);
        toast.success("Contadores SDS procesados exitosamente");
      } else if (type === "ers") {
        const res = await contadoresApi.processErs({
          customer_id: targetId,
          customer_name: targetName,
          fecha_maxima: fechaMaxima,
        });
        setGeneratedCsv(res.csv_filename);
        toast.success("Telemetría ERS procesada exitosamente");
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al procesar el cliente";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <h2 className="text-sm font-bold text-foreground">{titleMap[type]}</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="rounded-xl border border-primary/20 bg-primary/5 p-3">
          <p className="text-xs font-semibold text-primary">Cliente seleccionando:</p>
          <p className="text-sm font-bold text-foreground mt-0.5">{targetName}</p>
        </div>

        <form onSubmit={handleProcess} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Fecha Máxima de Lectura
            </label>
            <input
              type="date"
              value={fechaMaxima}
              onChange={(e) => setFechaMaxima(e.target.value)}
              className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm"
              required
            />
          </div>

          {generatedCsv && (
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 space-y-2">
              <p className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                Archivo CSV Generado:
              </p>
              <a
                href={contadoresApi.getOutputUrl(generatedCsv)}
                download={generatedCsv}
                className="flex items-center gap-2 rounded-xl bg-emerald-600 px-3.5 py-2 text-xs font-bold text-white shadow-sm hover:bg-emerald-700 transition-all"
              >
                <Download className="h-4 w-4" />
                Descargar {generatedCsv}
              </a>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-3 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl px-4 py-2 text-xs font-semibold text-muted-foreground hover:bg-muted"
            >
              Cerrar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2 text-xs font-bold text-primary-foreground shadow-md hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              Procesar y Generar CSV
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
