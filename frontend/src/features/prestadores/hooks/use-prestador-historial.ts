import { useEffect, useState } from "react";
import { prestadoresApi } from "../api/prestadores-api";
import type { AsignacionHistorial } from "../types/prestadores";

/** Historial de reasignación de operador de un PST. `null` mientras carga. */
export function usePrestadorHistorial(prestadorId: string): AsignacionHistorial[] | null {
  const [historial, setHistorial] = useState<AsignacionHistorial[] | null>(null);

  // Ajustar estado durante el render (no en el efecto) al cambiar de PST —
  // mismo patrón que sla-detail.tsx/ftp-client-modal.tsx.
  const [prevPrestadorId, setPrevPrestadorId] = useState(prestadorId);
  if (prestadorId !== prevPrestadorId) {
    setPrevPrestadorId(prestadorId);
    setHistorial(null);
  }

  useEffect(() => {
    let active = true;
    prestadoresApi.listHistorial(prestadorId).then((items) => {
      if (active) setHistorial(items);
    });
    return () => {
      active = false;
    };
  }, [prestadorId]);

  return historial;
}
