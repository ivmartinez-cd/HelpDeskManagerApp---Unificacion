"use client";

import { useEffect, useState } from "react";
import { despachadosApi } from "../api/despachados-api";
import type { ReclamoOca } from "../types/despachados";
import { mensajeDeError } from "./use-despachados-listado";

/** Datos para precargar el reclamo en OCA (`GET /reclamo-oca`) de una guía.
 * `loading` sigue en true hasta que llega el reclamo o falla. */
export function useReclamoOca(guia: string) {
  const [reclamo, setReclamo] = useState<ReclamoOca | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    despachadosApi.getReclamoOca(guia).then(
      (r) => {
        if (vigente) setReclamo(r);
      },
      (err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudieron preparar los datos del reclamo"));
      },
    );
    return () => {
      vigente = false;
    };
  }, [guia]);

  return { reclamo, error, loading: reclamo === null && error === null };
}
