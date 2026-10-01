"use client";

import { useCallback, useEffect, useState } from "react";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  PropuestasVinculo,
  ResultadoVinculoTablaKmSpst,
  Spst,
  SyncSigesResult,
  SyncTarifariosResult,
  ZonasSiges,
} from "../types/liquidaciones";

// Simulaciones (dry-run) que abren los modales de Siges. Promise-chain en vez
// de async/await: react-hooks/set-state-in-effect solo acepta setState en
// callbacks .then/.catch. Los setters quedan expuestos porque el "Aplicar" del
// modal reemplaza el resultado simulado por el real.

/** Propuestas de vínculo + dry-run del sync de prestadores/SPST. El modal se
 * monta solo abierto, así que corre una vez por apertura. */
export function useSigesSyncPreview() {
  const [propuestas, setPropuestas] = useState<PropuestasVinculo | null>(null);
  const [resultado, setResultado] = useState<SyncSigesResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(
    () =>
      Promise.all([liquidacionesApi.getSigesPropuestas(), liquidacionesApi.syncSiges(true)])
        .then(([props, dry]) => {
          setPropuestas(props);
          setResultado(dry);
          setError(null);
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Error al consultar");
        }),
    [],
  );

  useEffect(() => { void refetch(); }, [refetch]);

  return { propuestas, setPropuestas, resultado, setResultado, error, setError, refetch };
}

/** Zonas de Siges del prestador + dry-run del sync de tarifarios + sus SPST. */
export function useSigesTarifariosPreview(prestadorId: string) {
  const [zonas, setZonas] = useState<ZonasSiges | null>(null);
  const [spsts, setSpsts] = useState<Spst[]>([]);
  const [resultado, setResultado] = useState<SyncTarifariosResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(
    () =>
      Promise.all([
        liquidacionesApi.getSigesZonas(prestadorId),
        liquidacionesApi.syncTarifariosSiges(true, prestadorId),
        liquidacionesApi.listSpsts({ prestadorId }),
      ])
        .then(([z, dry, s]) => {
          setZonas(z);
          setResultado(dry);
          setSpsts(s);
          setError(null);
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Error al consultar");
        }),
    [prestadorId],
  );

  useEffect(() => { void refetch(); }, [refetch]);

  return { zonas, spsts, resultado, setResultado, error, refetch };
}

/** Dry-run del vínculo de filas de Tabla KM a SPST por localidad/provincia. */
export function useVinculoSpstPreview(prestadorId: string, incluirProvincia: boolean) {
  const [resultado, setResultado] = useState<ResultadoVinculoTablaKmSpst | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(
    () =>
      liquidacionesApi
        .vincularSpstTablaKm(prestadorId, true, incluirProvincia)
        .then((r) => { setResultado(r); setError(null); })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Error al calcular vínculos");
        }),
    [prestadorId, incluirProvincia],
  );

  useEffect(() => { void refetch(); }, [refetch]);

  return { resultado, setResultado, error };
}
