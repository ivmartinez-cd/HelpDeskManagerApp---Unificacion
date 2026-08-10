"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Calculator } from "lucide-react";
import { contadoresApi, type ManualEstimationResponse } from "../api/contadores-api";
import { Card, CardHeader, CardBody } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import { Button } from "@/shared/components/ui/button";
import { StatCard } from "@/shared/components/ui/stat-card";
import { EmptyState } from "@/shared/components/ui/empty-state";

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
      <Card>
        <CardHeader title="Datos para la Estimación Manual" icon={Calculator} />
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Input
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
              <Input
                id="calc-contador-final"
                label="Contador Final"
                type="number"
                min="0"
                value={contadorFinal}
                onChange={(e) =>
                  setContadorFinal(e.target.value === "" ? "" : Number(e.target.value))
                }
                placeholder="Ej: 15000"
                required
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <Input
                id="calc-fecha-inicial"
                label="Fecha Lectura Inicial"
                type="date"
                value={fechaInicial}
                onChange={(e) => setFechaInicial(e.target.value)}
                required
              />
              <Input
                id="calc-fecha-final"
                label="Fecha Lectura Final"
                type="date"
                value={fechaFinal}
                onChange={(e) => setFechaFinal(e.target.value)}
                required
              />
            </div>

            <Input
              id="calc-fecha-estimacion"
              label="Fecha Objetivo de Estimación"
              type="date"
              value={fechaEstimacion}
              onChange={(e) => setFechaEstimacion(e.target.value)}
              required
            />

            <Button type="submit" loading={loading} className="mt-2 w-full">
              <Calculator className="h-4 w-4" />
              Calcular Estimación
            </Button>
          </form>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Resultado del Cálculo" />
        <CardBody>
          {result ? (
            <div className="space-y-4">
              <div className="rounded-xl border border-accent/20 bg-accent/5 p-5 text-center">
                <p className="text-xs font-semibold uppercase tracking-wider text-accent">
                  Contador Estimado Recomendado
                </p>
                <p className="mt-2 text-4xl font-black text-foreground">
                  {Math.round(result.contador_estimado).toLocaleString()}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  (Valor exacto: {result.contador_estimado.toFixed(2)})
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <StatCard label="Días de Muestra" value={`${result.dias_muestra} días`} />
                <StatCard
                  label="Consumo de Muestra"
                  value={result.consumo_muestra.toLocaleString()}
                />
                <StatCard
                  label="Consumo Diario Promedio"
                  value={`${result.consumo_diario.toFixed(2)} / día`}
                />
                <StatCard label="Días a Estimar" value={`${result.dias_estimados} días`} />
              </div>
            </div>
          ) : (
            <EmptyState
              icon={Calculator}
              title="Sin resultados todavía"
              description='Ingresá los datos a la izquierda y hacé clic en "Calcular Estimación"'
            />
          )}
        </CardBody>
      </Card>
    </div>
  );
}
