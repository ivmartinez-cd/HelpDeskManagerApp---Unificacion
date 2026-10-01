"use client";

import { useEffect, useState } from "react";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { GeocodeCandidato } from "../types/liquidaciones";

/** Candidatos de geocode del domicilio de una fila de Tabla KM. */
export function useCandidatosLugar(filaId: string) {
  const [candidatos, setCandidatos] = useState<GeocodeCandidato[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    liquidacionesApi
      .buscarLugarFila(filaId)
      .then((r) => setCandidatos(r.candidatos))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error al buscar lugar"));
  }, [filaId]);

  return { candidatos, error };
}
