"use client";

import { useEffect, useState } from "react";
import { bonoTecnicosApi } from "../api/bono-tecnicos-api";
import type { IncidenteBono } from "../types/bono-tecnicos";
import { monthValueToPeriodo } from "./use-bono-tecnicos";

/** Incidentes del técnico autenticado para un mes (`YYYY-MM`, el valor del
 * `<input type="month">`). Chequea el vínculo Empleado↔Siges antes de pedir
 * la lista (mismo criterio que `useMiResumenBono`): sin vínculo,
 * `vinculado=false` y la pantalla lo explica, no se muestra como error. */
export function useMisIncidentes(monthValue: string) {
  const [incidentes, setIncidentes] = useState<IncidenteBono[]>([]);
  const [vinculado, setVinculado] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Resetear al cambiar de mes durante el render, no en el efecto (mismo
  // patrón que use-bono-tecnicos.ts).
  const [prevMonthValue, setPrevMonthValue] = useState(monthValue);
  if (monthValue !== prevMonthValue) {
    setPrevMonthValue(monthValue);
    setLoading(true);
    setError(null);
    setIncidentes([]);
  }

  useEffect(() => {
    let active = true;
    async function cargar() {
      try {
        const { vinculado: v } = await bonoTecnicosApi.getVinculoSiges();
        const data = v ? await bonoTecnicosApi.getMisIncidentes(monthValueToPeriodo(monthValue)) : [];
        if (!active) return;
        setVinculado(v);
        setIncidentes(data);
      } catch (err: unknown) {
        console.error("Error al cargar mis incidentes:", err);
        if (active) setError(err instanceof Error ? err.message : "No se pudieron cargar tus incidentes.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void cargar();
    return () => {
      active = false;
    };
  }, [monthValue]);

  return { incidentes, vinculado, loading, error };
}
