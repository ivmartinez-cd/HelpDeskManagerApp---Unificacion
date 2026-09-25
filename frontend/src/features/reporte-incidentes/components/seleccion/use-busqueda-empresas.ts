"use client";

import { useEffect, useState } from "react";
import { reporteIncidentesApi } from "../../api/reporte-incidentes-api";
import type { Empresa } from "../../types/reporte";

/** El legacy mostraba como mucho 50 coincidencias. */
export const MAX_RESULTADOS = 50;
const DEMORA_MS = 250;

interface Respuesta {
  consulta: string;
  resultados: Empresa[];
  total: number;
  error: string | null;
}

/** Busca clientes en el backend (nombre sin acentos o ID) con debounce.
 * `cargando` mientras la última respuesta no sea de la consulta actual. */
export function useBusquedaEmpresas(consulta: string) {
  const [respuesta, setRespuesta] = useState<Respuesta | null>(null);

  useEffect(() => {
    let activo = true;
    const timer = setTimeout(() => {
      reporteIncidentesApi
        .listEmpresas(consulta.trim(), MAX_RESULTADOS)
        .then((pagina) => {
          if (activo) setRespuesta({ consulta, resultados: pagina.items, total: pagina.total, error: null });
        })
        .catch((err: unknown) => {
          if (!activo) return;
          console.error("Error al buscar clientes del reporte de incidentes:", err);
          setRespuesta({ consulta, resultados: [], total: 0, error: "No se pudo cargar la lista de clientes." });
        });
    }, DEMORA_MS);
    return () => {
      activo = false;
      clearTimeout(timer);
    };
  }, [consulta]);

  return {
    resultados: respuesta?.resultados ?? [],
    total: respuesta?.total ?? 0,
    error: respuesta?.error ?? null,
    cargando: respuesta?.consulta !== consulta,
  };
}
