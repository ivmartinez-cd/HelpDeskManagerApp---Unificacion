"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Download, Sigma } from "lucide-react";
import { contadoresApi, type FixedSumResponse } from "../api/contadores-api";
import {
  BrandButton,
  BrandFileInput,
  BrandInput,
  BrandResultPanel,
  BrandStatTile,
  brandButtonClasses,
} from "@/shared/components/ui/brand-form";

export function SumaFijaTool() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [fecha, setFecha] = useState(new Date().toISOString().split("T")[0]);
  const [hojas, setHojas] = useState<number | "">(500);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FixedSumResponse | null>(null);

  const handleSubmit = async (e: FormEvent) => {
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
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="grid gap-5 md:grid-cols-3">
          <BrandFileInput
            id="suma-fija-files"
            label="Archivos Excel (.xlsx)"
            accept=".xlsx"
            multiple
            onChange={(e) => setFiles(e.target.files)}
            required
          />
          <BrandInput
            id="suma-fija-fecha"
            label="Fecha de Lectura"
            type="date"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
            required
          />
          <BrandInput
            id="suma-fija-hojas"
            label="Hojas a Sumar"
            type="number"
            min="1"
            value={hojas}
            onChange={(e) => setHojas(e.target.value === "" ? "" : Number(e.target.value))}
            placeholder="Ej: 500"
            required
          />
        </div>

        <BrandButton type="submit" loading={loading} className="self-start">
          <Sigma className="h-4 w-4" />
          Procesar Suma Fija
        </BrandButton>
      </form>

      {result && (
        <BrandResultPanel title="Resultado del Procesamiento">
          <div className="max-w-xs">
            <BrandStatTile label="Total Filas Generadas" value={result.total_rows} />
          </div>

          <div className="mt-6 flex flex-col gap-3">
            <p className="font-body text-xs font-bold uppercase tracking-wider text-[#7a7a7a]">
              Archivos CSV Generados ({result.csv_filenames.length}):
            </p>
            <div className="flex flex-wrap gap-3">
              {result.csv_filenames.map((fname) => (
                <a
                  key={fname}
                  href={contadoresApi.getOutputUrl(fname)}
                  download={fname}
                  className={brandButtonClasses({ variant: "primary", size: "sm" })}
                >
                  <Download className="h-4 w-4" />
                  Descargar {fname}
                </a>
              ))}
            </div>
          </div>
        </BrandResultPanel>
      )}
    </div>
  );
}
