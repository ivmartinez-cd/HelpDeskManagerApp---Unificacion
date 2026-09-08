"use client";

import { useEffect, useState } from "react";
import { bonoTecnicosApi } from "../api/bono-tecnicos-api";
import type { EvolucionEquipo, EvolucionTecnico } from "../types/bono-tecnicos";

function anioActual(): number {
  return new Date().getFullYear();
}

export function useBonoEvolucionAnual() {
  const [anio, setAnio] = useState<number>(anioActual());
  const [tecnicos, setTecnicos] = useState<EvolucionTecnico[]>([]);
  const [equipo, setEquipo] = useState<EvolucionEquipo | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Resetear datos al cambiar de año — mismo patrón que use-bono-tecnicos.ts.
  const [prevAnio, setPrevAnio] = useState(anio);
  if (anio !== prevAnio) {
    setPrevAnio(anio);
    setLoading(true);
    setError(null);
    setTecnicos([]);
    setEquipo(null);
  }

  useEffect(() => {
    let active = true;
    Promise.all([
      bonoTecnicosApi.getEvolucionAnual(anio),
      bonoTecnicosApi.getEvolucionEquipo(anio),
    ])
      .then(([tecnicosResult, equipoResult]) => {
        if (!active) return;
        setTecnicos(tecnicosResult);
        setEquipo(equipoResult);
      })
      .catch((err: unknown) => {
        if (!active) return;
        console.error("Error al cargar la evolución anual del bono:", err);
        setError(
          err instanceof Error ? err.message : "No se pudo cargar la evolución anual.",
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [anio]);

  return { anio, setAnio, tecnicos, equipo, loading, error };
}
