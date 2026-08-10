"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Download, FileCode } from "lucide-react";
import { contadoresApi, type Db3ExportResponse } from "../api/contadores-api";
import {
  BrandButton,
  BrandFileInput,
  BrandInput,
  BrandResultPanel,
  BrandStatTile,
  brandButtonClasses,
} from "@/shared/components/ui/brand-form";

export function Db3Tool() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [fechaMaxima, setFechaMaxima] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Db3ExportResponse | null>(null);

  const handleSubmit = async (e: FormEvent) => {
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
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="grid gap-5 md:grid-cols-2">
          <BrandFileInput
            id="db3-files"
            label="Archivos SQLite (.db3)"
            accept=".db3,.sqlite"
            multiple
            onChange={(e) => setFiles(e.target.files)}
            hint="Podés seleccionar múltiples archivos .db3 simultáneamente."
            required
          />
          <BrandInput
            id="db3-fecha-maxima"
            label="Fecha Máxima de Lectura (Opcional)"
            type="date"
            value={fechaMaxima}
            onChange={(e) => setFechaMaxima(e.target.value)}
          />
        </div>

        <BrandButton type="submit" loading={loading} className="self-start">
          <FileCode className="h-4 w-4" />
          Procesar DB3 a CSV
        </BrandButton>
      </form>

      {result && (
        <BrandResultPanel title="Resultado de Consolidación">
          <div className="max-w-xs">
            <BrandStatTile label="Total Filas Generadas" value={result.rowCount} />
          </div>

          {result.warnings.length > 0 && (
            <ul className="mt-4 flex flex-col gap-1 rounded-[10px] border border-amber-500/20 bg-amber-500/5 p-3 font-body text-xs text-amber-700">
              {result.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          )}

          <a
            href={contadoresApi.getOutputUrl(result.csvFile)}
            download={result.csvFile}
            className={`${brandButtonClasses({ variant: "primary" })} mt-6`}
          >
            <Download className="h-4 w-4" />
            Descargar Archivo CSV Consolidado (.csv)
          </a>
        </BrandResultPanel>
      )}
    </div>
  );
}
