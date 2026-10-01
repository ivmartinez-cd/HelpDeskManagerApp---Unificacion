"use client";

import { useEffect, useState } from "react";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { SucursalPropia } from "../types/liquidaciones";

/** Sucursales propias del PST en Siges (candidatas a base de despacho). El
 * error de carga va a `onError`, que comparte el mensaje con el del guardado
 * en el componente. Con `enabled` en false no pide nada. */
export function useSucursalesPropias(prestadorId: string, onError: (msg: string) => void, enabled = true) {
  const [sucursales, setSucursales] = useState<SucursalPropia[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!enabled) return;
    liquidacionesApi
      .listSucursalesPropiasPrestatdor(prestadorId)
      .then(setSucursales)
      .catch((e: unknown) => onError(e instanceof Error ? e.message : "Error al cargar sucursales"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prestadorId, enabled]);

  return { sucursales, loading };
}
