"use client";

import { useEffect, useState } from "react";
import { bonoTecnicosApi } from "../api/bono-tecnicos-api";
import type { CrearSolicitudTvBody, SolicitudTv } from "../types/bono-tecnicos";
import { monthValueToPeriodo } from "./use-bono-tecnicos";

function currentMonthValue(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export function useMisSolicitudesTv() {
  const [monthValue, setMonthValue] = useState<string>(currentMonthValue());
  const [solicitudes, setSolicitudes] = useState<SolicitudTv[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Mismo patrón que use-bono-tecnicos.ts: ajustar estado durante el render
  // al cambiar de período, no dentro del efecto (react-hooks/set-state-in-effect).
  const [prevMonthValue, setPrevMonthValue] = useState(monthValue);
  if (monthValue !== prevMonthValue) {
    setPrevMonthValue(monthValue);
    setLoading(true);
    setError(null);
    setSolicitudes([]);
  }

  const cargar = () => {
    const periodo = monthValueToPeriodo(monthValue);
    return bonoTecnicosApi
      .getMisSolicitudes(periodo)
      .then(setSolicitudes)
      .catch((err: unknown) => {
        console.error("Error al cargar mis solicitudes de TV:", err);
        setError(
          err instanceof Error ? err.message : "No se pudieron cargar las solicitudes.",
        );
      });
  };

  useEffect(() => {
    let active = true;
    cargar().finally(() => {
      if (active) setLoading(false);
    });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monthValue]);

  const enviarSolicitud = (body: CrearSolicitudTvBody) => {
    setSubmitting(true);
    setError(null);
    return bonoTecnicosApi
      .crearSolicitud(body)
      .then(() => cargar())
      .catch((err: unknown) => {
        console.error("Error al enviar la solicitud de TV:", err);
        setError(err instanceof Error ? err.message : "No se pudo enviar la solicitud.");
        throw err;
      })
      .finally(() => setSubmitting(false));
  };

  return {
    monthValue,
    setMonthValue,
    solicitudes,
    loading,
    submitting,
    error,
    enviarSolicitud,
  };
}
