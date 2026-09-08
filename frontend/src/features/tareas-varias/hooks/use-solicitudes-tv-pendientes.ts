"use client";

import { useEffect, useState } from "react";
import { tareasVariasApi } from "../api/tareas-varias-api";
import type { CrearSolicitudTvAdminBody, SolicitudTv } from "../types/tareas-varias";

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
    return tareasVariasApi
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
    return tareasVariasApi
      .decidirSolicitud(id, { decision, motivo })
      .then(() => cargar())
      .catch((err: unknown) => {
        console.error("Error al decidir la solicitud de TV:", err);
        setError(err instanceof Error ? err.message : "No se pudo procesar la decisión.");
      })
      .finally(() => setDecidingId(null));
  };

  // Nace ya APROBADA (ver CrearSolicitudTvAdminBody): no aparece en la cola
  // de PENDIENTE, así que no hace falta recargar `solicitudes` después — el
  // propio modal maneja su `saving`/error (ver `useModalSubmit`).
  const crearAdmin = (idTecnico: number, body: CrearSolicitudTvAdminBody) =>
    tareasVariasApi.crearSolicitudAdmin(idTecnico, body);

  return { solicitudes, loading, decidingId, error, decidir, crearAdmin };
}
