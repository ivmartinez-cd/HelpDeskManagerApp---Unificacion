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
  const [zonaAnterior, setZonaAnterior] = useState(zona);

  // Al cambiar de zona se limpian los puntos ANTES de re-consultar: sin esto
  // quedan visibles los pines de la zona anterior mientras llega la nueva
  // (la caché puede estar fría, ~5-10s) sin ningún indicio de carga. Ajuste
  // de estado durante el render (no en un efecto) — patrón recomendado para
  // resetear estado derivado de un cambio de prop, sin el flash de un commit
  // extra ni el lint de setState síncrono en efectos.
  if (zona !== zonaAnterior) {
    setZonaAnterior(zona);
    setPuntos(null);
    setConsultadoEn(null);
    setError(null);
  }

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

  const refrescar = () => setRefreshToken((t) => t + 1);

  const geocodificar = () => {
    setGeocodificando(true);
    preventivosApi
      .geocodificarSucursales()
      .then((resultado) => {
        const reconciliadasInfo =
          resultado.reconciliadas > 0
            ? `, ${numberFormat.format(resultado.reconciliadas)} reconciliadas (Siges se corrigió solo)`
            : "";
        toast.success(
          `Geocodificación: ${numberFormat.format(resultado.resueltas)} resueltas, ` +
            `${numberFormat.format(resultado.ambiguas)} ambiguas, ` +
            `${numberFormat.format(resultado.sin_resultados)} sin resultados${reconciliadasInfo}`,
        );
        refrescar();
      })
      .catch((err: unknown) => {
        console.error("Error al geocodificar sucursales:", err);
        toast.error("No se pudo geocodificar. Reintentá.");
      })
      .finally(() => setGeocodificando(false));
  };

  return { puntos, sinUbicar, consultadoEn, error, geocodificando, geocodificar, refrescar };
}
