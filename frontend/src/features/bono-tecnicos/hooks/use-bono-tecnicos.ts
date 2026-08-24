"use client";

import { useEffect, useState } from "react";
import { bonoTecnicosApi } from "../api/bono-tecnicos-api";
import type { PuntajeTecnico } from "../types/bono-tecnicos";
import { useSession } from "@/services/session-provider";

function currentMonthValue(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

export function monthValueToPeriodo(value: string): string {
  return value.replace("-", "");
}

export function useBonoTecnicos() {
  const { user, can } = useSession();
  const canUpdate = user.isSuperadmin || can("bono-tecnicos", "update");

  const [monthValue, setMonthValue] = useState<string>(currentMonthValue());
  const [filas, setFilas] = useState<PuntajeTecnico[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Resetear datos al cambiar de período — "ajustar estado durante el
  // render" en vez de dentro del efecto (mismo patrón que use-sla-detail.ts).
  const [prevMonthValue, setPrevMonthValue] = useState(monthValue);
  if (monthValue !== prevMonthValue) {
    setPrevMonthValue(monthValue);
    setLoading(true);
    setError(null);
    setFilas([]);
  }

  const cargar = () => {
    const periodo = monthValueToPeriodo(monthValue);
    return bonoTecnicosApi
      .getResumen(periodo)
      .then(setFilas)
      .catch((err: unknown) => {
        console.error("Error al cargar el bono de técnicos:", err);
        setError(
          err instanceof Error ? err.message : "No se pudo cargar el bono de técnicos.",
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

  const guardarInput = (idTecnico: number, dias: number, tareasVarias: number) => {
    const fila = filas.find((f) => f.id_tecnico === idTecnico);
    if (!fila) return Promise.resolve();
    const periodo = monthValueToPeriodo(monthValue);
    setSavingId(idTecnico);
    setError(null);
    return bonoTecnicosApi
      .guardarInput(periodo, idTecnico, {
        tecnico: fila.tecnico,
        dias,
        tareas_varias: tareasVarias,
      })
      .then(cargar)
      .catch((err: unknown) => {
        console.error("Error al guardar Días/TV:", err);
        setError(err instanceof Error ? err.message : "No se pudo guardar el dato.");
      })
      .finally(() => setSavingId(null));
  };

  return {
    canUpdate,
    monthValue,
    setMonthValue,
    filas,
    loading,
    savingId,
    error,
    guardarInput,
  };
}
