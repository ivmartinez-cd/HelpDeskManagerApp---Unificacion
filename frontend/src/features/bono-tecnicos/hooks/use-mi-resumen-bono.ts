"use client";

import { useEffect, useState } from "react";
import { bonoTecnicosApi } from "../api/bono-tecnicos-api";
import type { MiResumenBono } from "../types/bono-tecnicos";

/** Puntaje/conteos/TV del técnico autenticado para un período — 404 si no
 * está vinculado a un técnico de Siges (se trata como "sin datos", no error
 * visible: no es algo que el técnico pueda resolver él mismo). */
export function useMiResumenBono(periodo?: string) {
  const [data, setData] = useState<MiResumenBono | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    bonoTecnicosApi
      .getMiResumen(periodo)
      .then((d) => active && setData(d))
      .catch((err: unknown) => {
        console.error("Error al cargar mi resumen de bono:", err);
        if (active) setError(err instanceof Error ? err.message : "No se pudo cargar tu bono.");
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [periodo]);

  return { data, loading, error };
}
