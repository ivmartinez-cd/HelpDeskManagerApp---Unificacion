"use client";

import { useEffect, useState } from "react";
import { preventivosApi } from "../api/preventivos-api";
import type { EstadoPreventivo, PuntoMapaPreventivo } from "../types/preventivos";

interface UsePuntosMapaParams {
  activo: boolean;
  zona: string | null;
  estado: string;
  soloHabilitados: boolean;
  busquedaAplicada: string;
}

/** Mismos filtros aplicados que la tabla (`usePreventivosView`); solo
 * consulta mientras la vista de mapa está activa, para no pagar una pasada
 * extra por Siges cuando el usuario nunca la abre. */
export function usePuntosMapa({
  activo,
  zona,
  estado,
  soloHabilitados,
  busquedaAplicada,
}: UsePuntosMapaParams) {
  const [puntos, setPuntos] = useState<PuntoMapaPreventivo[] | null>(null);
  const [sinUbicar, setSinUbicar] = useState(0);
  const [consultadoEn, setConsultadoEn] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activo || !zona) return;
    let cancelado = false;
    preventivosApi
      .listPuntosMapa({
        zona,
        estado: (estado || undefined) as EstadoPreventivo | undefined,
        habilitado: soloHabilitados ? true : undefined,
        q: busquedaAplicada || undefined,
      })
      .then((page) => {
        if (cancelado) return;
        setPuntos(page.items);
        setSinUbicar(page.sin_ubicar);
        setConsultadoEn(page.consultado_en);
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelado) return;
        console.error("Error al cargar el mapa de preventivos:", err);
        setError("No se pudo consultar el mapa. Reintentá.");
      });
    return () => {
      cancelado = true;
    };
  }, [activo, zona, estado, soloHabilitados, busquedaAplicada]);

  return { puntos, sinUbicar, consultadoEn, error };
}
