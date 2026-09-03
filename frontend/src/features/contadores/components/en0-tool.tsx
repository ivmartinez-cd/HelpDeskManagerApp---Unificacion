"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Download, FileSpreadsheet } from "lucide-react";
import { contadoresApi, type EstimationZeroResponse } from "../api/contadores-api";
import {
  BrandButton,
  BrandFileInput,
  BrandInput,
  BrandResultPanel,
  brandButtonClasses,
} from "@/shared/components/ui/brand-form";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { SigesLoadingModal } from "@/shared/components/ui/siges-loading-modal";

type Modo = "proceso" | "csv";

const MODOS = [
  { value: "proceso", label: "Por Nro de Proceso" },
  { value: "csv", label: "Subir CSV" },
];

export function En0Tool() {
  const [modo, setModo] = useState<Modo>("proceso");
  const [nroProceso, setNroProceso] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fecha, setFecha] = useState(new Date().toISOString().split("T")[0]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EstimationZeroResponse | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!fecha || (modo === "proceso" ? !nroProceso : !file)) {
      toast.error("Por favor completá todos los campos");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const res =
        modo === "proceso"
          ? await contadoresApi.runEstimationZeroFromProceso({
              nro_proceso: Number(nroProceso),
              fecha,
            })
          : await contadoresApi.runEstimationZero(buildFormData(file!, fecha));
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
    <div className="flex flex-col gap-6">
      <SegmentedControl
        label="Origen de los datos"
        options={MODOS}
        value={modo}
        onChange={(v) => setModo(v as Modo)}
      />

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="grid gap-5 md:grid-cols-2">
          {modo === "proceso" ? (
            <BrandInput
              id="en0-nro-proceso"
              label="Nro de Proceso"
              type="number"
              value={nroProceso}
              onChange={(e) => setNroProceso(e.target.value)}
              placeholder="Ej: 99070"
              required
            />
          ) : (
            <BrandFileInput
              id="en0-file"
              label="Archivo CSV / Falta Contador"
              accept=".csv,.txt"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              required
            />
          )}
          <BrandInput
            id="en0-fecha"
            label="Fecha de Lectura"
            type="date"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
            required
          />
        </div>

        <BrandButton type="submit" loading={loading} className="self-start">
          <FileSpreadsheet className="h-4 w-4" />
          Procesar Estimación en 0
        </BrandButton>
      </form>

      {loading && modo === "proceso" && (
        <SigesLoadingModal
          etapas={[
            { hasta: 5, texto: "Consultando el proceso en Siges…" },
            { texto: "La base está lenta hoy — seguimos esperando la respuesta…" },
          ]}
          nota="Trae las filas del proceso directo de Siges (sin caché: cada Nro de Proceso es una consulta nueva)."
        />
      )}

      {result && (
        <BrandResultPanel title="Resultado del Procesamiento">
          <a
            href={contadoresApi.getOutputUrl(result.file)}
            download={result.file}
            className={brandButtonClasses({ variant: "primary" })}
          >
            <Download className="h-4 w-4" />
            Descargar Archivo CSV Resultado (.csv)
          </a>
        </BrandResultPanel>
      )}
    </div>
  );
}

function buildFormData(file: File, fecha: string): FormData {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("fecha", fecha);
  return formData;
}
