"use client";

import { useCallback, useEffect, useState } from "react";
import { modificacionesApi } from "../api/modificaciones-api";
import type { ModificacionPrestador } from "../types/modificacion";

/** Cambios que el prestador aplicó sobre una liquidación (ADR-038). No pisa
 * `loading` de nuevo en un refetch (tras "Marcar como vistas") para no
 * parpadear — mismo patrón que `useWatiPendientesPolling`: arranca en `true`
 * y solo se apaga una vez, en el primer `finally`. */
export function useModificacionesLiquidacion(liquidacionId: string) {
  const [items, setItems] = useState<ModificacionPrestador[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(() => {
    modificacionesApi
      .listByLiquidacion(liquidacionId, 1, 500)
      .then((pagina) => setItems(pagina.items))
      .catch((err: unknown) => {
        console.error("Error al cargar modificaciones del prestador:", err);
      })
      .finally(() => setLoading(false));
  }, [liquidacionId]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { items, loading, refetch };
}
