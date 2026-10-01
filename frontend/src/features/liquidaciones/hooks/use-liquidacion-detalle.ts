"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/services/http-client";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { EvolucionIncidentesItem, LiquidacionDetalle, PrestadorLiquidacion } from "../types/liquidaciones";

/** Detalle de una liquidación + catálogo de prestadores. `setDetalle` queda
 * expuesto para que los handlers reemplacen la liquidación actualizada sin
 * volver a pedir todo. */
export function useLiquidacionDetalle(id: string) {
  const [detalle, setDetalle] = useState<LiquidacionDetalle | null>(null);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const refetch = useCallback(
    () =>
      Promise.all([liquidacionesApi.get(id), liquidacionesApi.listPrestadores(false)])
        .then(([det, prest]) => {
          setDetalle(det);
          setPrestadores(prest);
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 404) setNotFound(true);
          else throw err;
        })
        .finally(() => setLoading(false)),
    [id],
  );

  useEffect(() => { void refetch(); }, [refetch]);

  // Refresh silencioso al abrir el detalle: reconcilia esta liquidación contra
  // AyC (estado, costos/km de incidentes) una sola vez por visita a la página.
  // Best-effort — un fallo acá nunca debe impedir ver el detalle ya cargado.
  const reconciliadoRef = useRef(false);
  useEffect(() => {
    if (!detalle || reconciliadoRef.current) return;
    reconciliadoRef.current = true;
    const { numeroLiquidacion, estado } = detalle.liquidacion;
    if (!numeroLiquidacion || estado === "aprobada" || estado === "cerrada") return;
    void liquidacionesApi
      .reconciliar(id)
      .catch(() => {})
      .then(() => refetch());
  }, [detalle, id, refetch]);

  return { detalle, setDetalle, prestadores, loading, notFound, refetch };
}

/** Histórico del prestador (todas sus liquidaciones, no solo esta) para el
 * gráfico de evolución — no bloquea el render del detalle si falla, y no se
 * re-pide en cada refresh silencioso (solo cambia si cambia de prestador). */
export function useEvolucionIncidentes(prestadorId: string | undefined) {
  const [evolucion, setEvolucion] = useState<EvolucionIncidentesItem[] | null>(null);

  useEffect(() => {
    if (!prestadorId) return;
    let cancelado = false;
    liquidacionesApi
      .getEvolucionIncidentes(prestadorId)
      .then((items) => { if (!cancelado) setEvolucion(items); })
      .catch((err: unknown) => {
        console.error("No se pudo cargar la evolución de incidentes del prestador", err);
        if (!cancelado) setEvolucion([]);
      });
    return () => { cancelado = true; };
  }, [prestadorId]);

  return evolucion;
}
