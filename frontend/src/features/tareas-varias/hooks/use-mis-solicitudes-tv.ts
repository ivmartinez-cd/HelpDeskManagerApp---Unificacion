"use client";

import { useEffect, useState } from "react";
import { bonoTecnicosApi } from "@/features/bono-tecnicos/api/bono-tecnicos-api";
import { tareasVariasApi } from "../api/tareas-varias-api";
import type { CrearSolicitudTvBody, SolicitudTv } from "../types/tareas-varias";

function currentMonthValue(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

/** "2026-05" (input `type=month`) -> "202605" (período AAAAMM del backend). */
export function monthValueToPeriodo(value: string): string {
  return value.replace("-", "");
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

  // Sin vínculo Empleado↔Siges no hay `id_tecnico`: `getMisSolicitudes`
  // tiraría 404 (un superadmin ve el módulo aunque no sea técnico, ver
  // `bonoTecnicosApi.getVinculoSiges`).
  const cargar = () => {
    const periodo = monthValueToPeriodo(monthValue);
    return bonoTecnicosApi
      .getVinculoSiges()
      .then(({ vinculado }) => (vinculado ? tareasVariasApi.getMisSolicitudes(periodo) : []))
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
    return tareasVariasApi
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
