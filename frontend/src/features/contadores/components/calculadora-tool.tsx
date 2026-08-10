"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Calculator } from "lucide-react";
import { contadoresApi, type ManualEstimationResponse } from "../api/contadores-api";
import {
  BrandButton,
  BrandEmptyState,
  BrandInput,
  BrandStatTile,
} from "@/shared/components/ui/brand-form";

export function CalculadoraTool() {
  const [contadorInicial, setContadorInicial] = useState<number | "">("");
  const [contadorFinal, setContadorFinal] = useState<number | "">("");
  const [fechaInicial, setFechaInicial] = useState<string>("");
  const [fechaFinal, setFechaFinal] = useState<string>("");
  const [fechaEstimacion, setFechaEstimacion] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ManualEstimationResponse | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (
      contadorInicial === "" ||
      contadorFinal === "" ||
      !fechaInicial ||
      !fechaFinal ||
      !fechaEstimacion
    ) {
      toast.error("Por favor completá todos los campos requeridos");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const res = await contadoresApi.runManualEstimation({
        contador_inicial: Number(contadorInicial),
        contador_final: Number(contadorFinal),
        fecha_inicial: fechaInicial,
        fecha_final: fechaFinal,
        fecha_estimacion: fechaEstimacion,
      });
      setResult(res);
      toast.success("Cálculo realizado con éxito");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al calcular la estimación";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <BrandInput
            id="calc-contador-inicial"
            label="Contador Inicial"
            type="number"
            min="0"
            value={contadorInicial}
            onChange={(e) =>
              setContadorInicial(e.target.value === "" ? "" : Number(e.target.value))
            }
            placeholder="Ej: 10000"
            required
          />
          <BrandInput
            id="calc-contador-final"
            label="Contador Final"
            type="number"
            min="0"
            value={contadorFinal}
            onChange={(e) => setContadorFinal(e.target.value === "" ? "" : Number(e.target.value))}
            placeholder="Ej: 15000"
            required
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <BrandInput
            id="calc-fecha-inicial"
            label="Fecha Lectura Inicial"
            type="date"
            value={fechaInicial}
            onChange={(e) => setFechaInicial(e.target.value)}
            required
          />
          <BrandInput
            id="calc-fecha-final"
            label="Fecha Lectura Final"
            type="date"
            value={fechaFinal}
            onChange={(e) => setFechaFinal(e.target.value)}
            required
          />
        </div>

        <BrandInput
          id="calc-fecha-estimacion"
          label="Fecha Objetivo de Estimación"
          type="date"
          value={fechaEstimacion}
          onChange={(e) => setFechaEstimacion(e.target.value)}
          required
        />

        <BrandButton type="submit" loading={loading} className="mt-2 w-full">
          <Calculator className="h-4 w-4" />
          Calcular Estimación
        </BrandButton>
      </form>

      <div>
        {result ? (
          <div className="flex flex-col gap-4">
            <div className="rounded-[10px] border border-brand-orange/20 bg-brand-orange/5 p-5 text-center">
              <p className="font-body text-xs font-semibold uppercase tracking-wider text-brand-orange">
                Contador Estimado Recomendado
              </p>
              <p className="mt-2 font-heading text-4xl font-extrabold text-brand-charcoal">
                {result.contEst.toLocaleString()}
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <BrandStatTile label="Días a Estimar" value={`${result.diasEst} días`} />
              <BrandStatTile
                label="Consumo Estimado en el Período"
                value={result.impEst.toLocaleString()}
              />
              <BrandStatTile
                label="Tasa de Consumo Diario"
                value={`${result.impDia.toFixed(2)} / día`}
              />
              <BrandStatTile
                label="Consumo Mensual Estimado"
                value={result.impMes.toLocaleString()}
              />
            </div>
          </div>
        ) : (
          <BrandEmptyState
            icon={Calculator}
            title="Sin resultados todavía"
            description='Ingresá los datos a la izquierda y hacé clic en "Calcular Estimación"'
          />
        )}
      </div>
    </div>
  );
}
