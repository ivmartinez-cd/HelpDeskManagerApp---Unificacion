"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Download } from "lucide-react";
import { contadoresApi } from "../api/contadores-api";
import { Modal } from "@/shared/components/ui/modal";
import { Input } from "@/shared/components/ui/input";
import { Button, buttonClasses } from "@/shared/components/ui/button";

interface Props {
  isOpen: boolean;
  type: "ftp" | "sds" | "ers";
  targetId: string;
  targetName: string;
  onClose: () => void;
}

const titleMap: Record<Props["type"], string> = {
  ftp: "Descargar y Procesar DB3 de Cliente FTP",
  sds: "Descargar Contadores HP SDS",
  ers: "Descargar Telemetría Epson ERS",
};

export function ProcessClientModal({ isOpen, type, targetId, targetName, onClose }: Props) {
  const [fechaMaxima, setFechaMaxima] = useState(new Date().toISOString().split("T")[0]);
  const [loading, setLoading] = useState(false);
  const [generatedCsv, setGeneratedCsv] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleProcess = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setGeneratedCsv(null);
    setError(null);

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
      } else {
        const res = await contadoresApi.processErs({
          customer_id: targetId,
          customer_name: targetName,
          fecha_maxima: fechaMaxima,
        });
        setGeneratedCsv(res.csv_filename);
        toast.success("Telemetría ERS procesada exitosamente");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al procesar el cliente");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={titleMap[type]} maxWidth="max-w-md" error={error}>
      <div className="mb-4 rounded-xl border border-accent/20 bg-accent/5 p-3">
        <p className="text-xs font-semibold text-accent">Cliente seleccionado:</p>
        <p className="mt-0.5 text-sm font-bold text-foreground">{targetName}</p>
      </div>

      <form onSubmit={handleProcess} className="space-y-4">
        <Input
          id="process-fecha-maxima"
          label="Fecha Máxima de Lectura"
          type="date"
          value={fechaMaxima}
          onChange={(e) => setFechaMaxima(e.target.value)}
          required
        />

        {generatedCsv && (
          <div className="space-y-2 rounded-xl border border-success/20 bg-success/5 p-3">
            <p className="text-xs font-semibold text-success">Archivo CSV Generado:</p>
            <a
              href={contadoresApi.getOutputUrl(generatedCsv)}
              download={generatedCsv}
              className={buttonClasses({ variant: "success", size: "sm" })}
            >
              <Download className="h-4 w-4" />
              Descargar {generatedCsv}
            </a>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cerrar
          </Button>
          <Button type="submit" loading={loading}>
            <Download className="h-4 w-4" />
            Procesar y Generar CSV
          </Button>
        </div>
      </form>
    </Modal>
  );
}
