"use client";

import { useEffect, useState } from "react";
import { bonoTecnicosApi } from "../api/bono-tecnicos-api";
import type { IncidenteBono } from "../types/bono-tecnicos";

/** Detalle de incidentes de un técnico/período — se monta con
 * `key={idTecnico}` desde el llamador para que el estado arranque limpio en
 * cada apertura del modal (mismo patrón que use-consumable-detail.ts de
 * insumos), en vez de resetear a mano en un efecto. */
export function useBonoTecnicoDetalle(periodo: string, idTecnico: number) {
  const [incidentes, setIncidentes] = useState<IncidenteBono[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    bonoTecnicosApi
      .getIncidentes(periodo, idTecnico)
      .then((data) => {
        if (active) setIncidentes(data);
      })
      .catch((err: unknown) => {
        if (!active) return;
        console.error("Error al cargar el detalle del bono:", err);
        setError(err instanceof Error ? err.message : "No se pudo cargar el detalle.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { incidentes, loading, error };
}
