"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { preventivosApi } from "../api/preventivos-api";
import type { EstadoPreventivo, PuntoMapaPreventivo } from "../types/preventivos";
import { numberFormat } from "../components/preventivos-format";

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
  const [geocodificando, setGeocodificando] = useState(false);
  const [refreshToken, setRefreshToken] = useState(0);

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
  }, [activo, zona, estado, soloHabilitados, busquedaAplicada, refreshToken]);

  const geocodificar = () => {
    setGeocodificando(true);
    preventivosApi
      .geocodificarSucursales()
      .then((resultado) => {
        toast.success(
          `Geocodificación: ${numberFormat.format(resultado.resueltas)} resueltas, ` +
            `${numberFormat.format(resultado.ambiguas)} ambiguas, ` +
            `${numberFormat.format(resultado.sin_resultados)} sin resultados`,
        );
        setRefreshToken((t) => t + 1);
      })
      .catch((err: unknown) => {
        console.error("Error al geocodificar sucursales:", err);
        toast.error("No se pudo geocodificar. Reintentá.");
      })
      .finally(() => setGeocodificando(false));
  };

  return { puntos, sinUbicar, consultadoEn, error, geocodificando, geocodificar };
}
