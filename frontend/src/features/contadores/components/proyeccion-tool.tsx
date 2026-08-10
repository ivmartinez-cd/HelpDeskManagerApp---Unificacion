"use client";

import { useId, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { ChevronDown, ChevronUp, Download, FileSpreadsheet, Sparkles } from "lucide-react";
import { contadoresApi, type ProyeccionResponse } from "../api/contadores-api";
import {
  BrandButton,
  BrandFileInput,
  BrandInput,
  BrandResultPanel,
  BrandStatTile,
  brandButtonClasses,
} from "@/shared/components/ui/brand-form";

export function ProyeccionTool() {
  const [file, setFile] = useState<File | null>(null);
  const [fechaToma, setFechaToma] = useState<string>(new Date().toISOString().split("T")[0]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ProyeccionResponse | null>(null);

  // Parámetros avanzados
  const [toleranciaDias, setToleranciaDias] = useState(2);
  const [minDiasIntervalo, setMinDiasIntervalo] = useState(1);
  const [ventanaRecienteDias, setVentanaRecienteDias] = useState(365);
  const [umbralMinimoConsumo, setUmbralMinimoConsumo] = useState(0.2);
  const [maxAntiguedadLecturaDias, setMaxAntiguedadLecturaDias] = useState(365);

  const advancedPanelId = useId();

  const handleSubmit = async (e: FormEvent) => {
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
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="grid gap-5 md:grid-cols-2">
          <BrandFileInput
            id="proyeccion-file"
            label="Archivo Excel de Contadores (.xlsx)"
            accept=".xlsx"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
          />
          <BrandInput
            id="proyeccion-fecha-toma"
            label="Fecha de Toma para Proyección"
            type="date"
            value={fechaToma}
            onChange={(e) => setFechaToma(e.target.value)}
            required
          />
        </div>

        <div className="rounded-[10px] border border-black/[0.1] bg-black/[0.02] p-4">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            aria-expanded={showAdvanced}
            aria-controls={advancedPanelId}
            className="flex w-full items-center justify-between font-body text-xs font-bold uppercase tracking-wider text-brand-charcoal"
          >
            <span>Parámetros del Algoritmo de Proyección</span>
            {showAdvanced ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>

          {showAdvanced && (
            <div
              id={advancedPanelId}
              className="mt-4 grid gap-4 border-t border-black/[0.08] pt-4 sm:grid-cols-2 lg:grid-cols-3"
            >
              <BrandInput
                id="proyeccion-tolerancia-dias"
                label="Tolerancia de días (Días)"
                type="number"
                value={toleranciaDias}
                onChange={(e) => setToleranciaDias(Number(e.target.value))}
              />
              <BrandInput
                id="proyeccion-min-dias-intervalo"
                label="Mínimo días intervalo"
                type="number"
                value={minDiasIntervalo}
                onChange={(e) => setMinDiasIntervalo(Number(e.target.value))}
              />
              <BrandInput
                id="proyeccion-ventana-reciente"
                label="Ventana reciente (Días)"
                type="number"
                value={ventanaRecienteDias}
                onChange={(e) => setVentanaRecienteDias(Number(e.target.value))}
              />
              <BrandInput
                id="proyeccion-umbral-consumo"
                label="Umbral mínimo consumo (/día)"
                type="number"
                step="0.01"
                value={umbralMinimoConsumo}
                onChange={(e) => setUmbralMinimoConsumo(Number(e.target.value))}
              />
              <BrandInput
                id="proyeccion-max-antiguedad"
                label="Máx. antigüedad lectura (Días)"
                type="number"
                value={maxAntiguedadLecturaDias}
                onChange={(e) => setMaxAntiguedadLecturaDias(Number(e.target.value))}
              />
            </div>
          )}
        </div>

        <BrandButton type="submit" loading={loading} className="self-start">
          <Sparkles className="h-4 w-4" />
          Ejecutar Proyección
        </BrandButton>
      </form>

      {result && (
        <BrandResultPanel title="Resultados de Proyección">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <BrandStatTile label="Total Series" value={result.total_series} />
            <BrandStatTile
              label="Proyectadas"
              value={result.series_proyectadas}
              tone="highlight"
            />
            <BrandStatTile label="Reales" value={result.series_reales} />
            <BrandStatTile label="Sin Datos / Insuficiente" value={result.series_sin_datos} />
          </div>

          <div className="mt-6 flex flex-wrap gap-3 border-t border-black/[0.08] pt-4">
            <a
              href={contadoresApi.getOutputUrl(result.xlsx_filename)}
              download={result.xlsx_filename}
              className={brandButtonClasses({ variant: "primary" })}
            >
              <FileSpreadsheet className="h-4 w-4" />
              Descargar Reporte Excel Completo (.xlsx)
            </a>
            <a
              href={contadoresApi.getOutputUrl(result.csv_filename)}
              download={result.csv_filename}
              className={brandButtonClasses({ variant: "outline" })}
            >
              <Download className="h-4 w-4" />
              Descargar CSV para SiGes (.csv)
            </a>
          </div>
        </BrandResultPanel>
      )}
    </div>
  );
}
