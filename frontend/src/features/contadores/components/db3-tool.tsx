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
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <BrandStatTile label="Total Filas Generadas" value={result.total_rows} />
            <BrandStatTile label="Clase 10 (Mono)" value={result.counterclass_10_count} />
            <BrandStatTile
              label="Clase 20 (Color)"
              value={result.counterclass_20_count}
              tone="highlight"
            />
            <BrandStatTile label="Clase 40 (Duplicados)" value={result.counterclass_40_count} />
          </div>

          <a
            href={contadoresApi.getOutputUrl(result.csv_filename)}
            download={result.csv_filename}
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
