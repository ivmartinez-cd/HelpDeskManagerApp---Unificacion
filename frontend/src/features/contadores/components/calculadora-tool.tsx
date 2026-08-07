"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Calculator, Calendar, Hash, Loader2 } from "lucide-react";
import { contadoresApi, type ManualEstimationResponse } from "../api/contadores-api";

export function CalculadoraTool() {
  const [contadorInicial, setContadorInicial] = useState<number | "">("");
  const [contadorFinal, setContadorFinal] = useState<number | "">("");
  const [fechaInicial, setFechaInicial] = useState<string>("");
  const [fechaFinal, setFechaFinal] = useState<string>("");
  const [fechaEstimacion, setFechaEstimacion] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ManualEstimationResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
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
      {/* Formulario */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
          <Calculator className="h-5 w-5 text-primary" />
          Datos para la Estimación Manual
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
                Contador Inicial
              </label>
              <div className="relative">
                <Hash className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  type="number"
                  min="0"
                  value={contadorInicial}
                  onChange={(e) =>
                    setContadorInicial(e.target.value === "" ? "" : Number(e.target.value))
                  }
                  placeholder="Ej: 10000"
                  className="w-full rounded-xl border border-input bg-background pl-9 pr-3 py-2 text-sm"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
                Contador Final
              </label>
              <div className="relative">
                <Hash className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  type="number"
                  min="0"
                  value={contadorFinal}
                  onChange={(e) =>
                    setContadorFinal(e.target.value === "" ? "" : Number(e.target.value))
                  }
                  placeholder="Ej: 15000"
                  className="w-full rounded-xl border border-input bg-background pl-9 pr-3 py-2 text-sm"
                  required
                />
              </div>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
                Fecha Lectura Inicial
              </label>
              <div className="relative">
                <Calendar className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  type="date"
                  value={fechaInicial}
                  onChange={(e) => setFechaInicial(e.target.value)}
                  className="w-full rounded-xl border border-input bg-background pl-9 pr-3 py-2 text-sm"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
                Fecha Lectura Final
              </label>
              <div className="relative">
                <Calendar className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  type="date"
                  value={fechaFinal}
                  onChange={(e) => setFechaFinal(e.target.value)}
                  className="w-full rounded-xl border border-input bg-background pl-9 pr-3 py-2 text-sm"
                  required
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
              Fecha Objetivo de Estimación
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="date"
                value={fechaEstimacion}
                onChange={(e) => setFechaEstimacion(e.target.value)}
                className="w-full rounded-xl border border-input bg-background pl-9 pr-3 py-2 text-sm"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-primary-foreground shadow-md shadow-primary/20 hover:bg-primary/90 transition-all disabled:opacity-50 mt-2"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Calculator className="h-4 w-4" />}
            Calcular Estimación
          </button>
        </form>
      </div>

      {/* Resultados */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm flex flex-col justify-between">
        <div>
          <h2 className="text-lg font-bold text-foreground mb-4">Resultado del Cálculo</h2>

          {result ? (
            <div className="space-y-4">
              <div className="rounded-xl border border-primary/20 bg-primary/5 p-5 text-center">
                <p className="text-xs font-semibold uppercase tracking-wider text-primary">
                  Contador Estimado Recomendado
                </p>
                <p className="text-4xl font-black text-foreground mt-2">
                  {Math.round(result.contador_estimado).toLocaleString()}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  (Valor exacto: {result.contador_estimado.toFixed(2)})
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-border bg-muted/20 p-3.5">
                  <p className="text-xs text-muted-foreground font-medium">Días de Muestra</p>
                  <p className="text-lg font-bold text-foreground mt-0.5">{result.dias_muestra} días</p>
                </div>
                <div className="rounded-xl border border-border bg-muted/20 p-3.5">
                  <p className="text-xs text-muted-foreground font-medium">Consumo de Muestra</p>
                  <p className="text-lg font-bold text-foreground mt-0.5">
                    {result.consumo_muestra.toLocaleString()}
                  </p>
                </div>
                <div className="rounded-xl border border-border bg-muted/20 p-3.5">
                  <p className="text-xs text-muted-foreground font-medium">Consumo Diario Promedio</p>
                  <p className="text-lg font-bold text-foreground mt-0.5">
                    {result.consumo_diario.toFixed(2)} / día
                  </p>
                </div>
                <div className="rounded-xl border border-border bg-muted/20 p-3.5">
                  <p className="text-xs text-muted-foreground font-medium">Días a Estimar</p>
                  <p className="text-lg font-bold text-foreground mt-0.5">{result.dias_estimados} días</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-dashed border-border p-6 text-center">
              <Calculator className="h-10 w-10 text-muted-foreground/40 mb-2" />
              <p className="text-sm font-medium text-muted-foreground">
                Ingresá los datos a la izquierda y hacé clic en &quot;Calcular Estimación&quot;
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
