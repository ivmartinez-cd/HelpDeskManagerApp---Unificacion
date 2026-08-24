"use client";

import { useEffect, useState } from "react";
import { bonoTecnicosApi } from "../api/bono-tecnicos-api";
import type { SolicitudTv } from "../types/bono-tecnicos";

export function useSolicitudesTvPendientes(periodo: string, enabled: boolean) {
  const [solicitudes, setSolicitudes] = useState<SolicitudTv[]>([]);
  const [loading, setLoading] = useState<boolean>(enabled);
  const [decidingId, setDecidingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Mismo patrón que use-bono-tecnicos.ts: ajustar estado durante el render
  // al cambiar de período/visibilidad, no dentro del efecto.
  const [prevKey, setPrevKey] = useState(`${periodo}:${enabled}`);
  const key = `${periodo}:${enabled}`;
  if (key !== prevKey) {
    setPrevKey(key);
    setLoading(enabled);
    setError(null);
    setSolicitudes([]);
  }

  const cargar = () => {
    if (!enabled) return Promise.resolve();
    return bonoTecnicosApi
      .getSolicitudesPendientes(periodo)
      .then(setSolicitudes)
      .catch((err: unknown) => {
        console.error("Error al cargar solicitudes de TV pendientes:", err);
        setError(
          err instanceof Error ? err.message : "No se pudieron cargar las solicitudes.",
        );
      });
  };

  useEffect(() => {
    if (!enabled) return;
    let active = true;
    cargar().finally(() => {
      if (active) setLoading(false);
    });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [periodo, enabled]);

  const decidir = (id: string, decision: "APROBADA" | "RECHAZADA", motivo?: string) => {
    setDecidingId(id);
    setError(null);
    return bonoTecnicosApi
      .decidirSolicitud(id, { decision, motivo })
      .then(() => cargar())
      .catch((err: unknown) => {
        console.error("Error al decidir la solicitud de TV:", err);
        setError(err instanceof Error ? err.message : "No se pudo procesar la decisión.");
      })
      .finally(() => setDecidingId(null));
  };

  return { solicitudes, loading, decidingId, error, decidir };
}
