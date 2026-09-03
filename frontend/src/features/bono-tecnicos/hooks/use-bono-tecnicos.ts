"use client";

import { useEffect, useState } from "react";
import { bonoTecnicosApi } from "../api/bono-tecnicos-api";
import type { CrearSolicitudTvAdminBody, PuntajeTecnico } from "../types/bono-tecnicos";
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
  const canApprove = user.isSuperadmin || can("bono-tecnicos", "approve");

  const [monthValue, setMonthValue] = useState<string>(currentMonthValue());
  const [filas, setFilas] = useState<PuntajeTecnico[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [savingSugeridos, setSavingSugeridos] = useState<boolean>(false);
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

  const guardarInput = (idTecnico: number, dias: number) => {
    const fila = filas.find((f) => f.id_tecnico === idTecnico);
    if (!fila) return Promise.resolve();
    const periodo = monthValueToPeriodo(monthValue);
    setSavingId(idTecnico);
    setError(null);
    return bonoTecnicosApi
      .guardarInput(periodo, idTecnico, { tecnico: fila.tecnico, dias })
      .then(cargar)
      .catch((err: unknown) => {
        console.error("Error al guardar Días:", err);
        setError(err instanceof Error ? err.message : "No se pudo guardar el dato.");
      })
      .finally(() => setSavingId(null));
  };

  // Aplica el sugerido a todos los técnicos "sin días cargados" de una — sin
  // esto había que hacer foco+blur celda por celda (ver EditableNumberCell)
  // para que cada uno dispare el guardado y el puntaje deje de mostrar "—".
  const cargarSugeridos = async () => {
    const pendientes = filas.filter((f) => f.dias === 0 && f.dias_sugeridos !== null);
    if (pendientes.length === 0) return;
    const periodo = monthValueToPeriodo(monthValue);
    setSavingSugeridos(true);
    setError(null);
    try {
      for (const fila of pendientes) {
        await bonoTecnicosApi.guardarInput(periodo, fila.id_tecnico, {
          tecnico: fila.tecnico,
          dias: fila.dias_sugeridos as number,
        });
      }
      await cargar();
    } catch (err) {
      console.error("Error al cargar los días sugeridos:", err);
      setError(err instanceof Error ? err.message : "No se pudo cargar los días sugeridos.");
    } finally {
      setSavingSugeridos(false);
    }
  };

  const crearSolicitudTvAdmin = (idTecnico: number, body: CrearSolicitudTvAdminBody) => {
    const periodo = monthValueToPeriodo(monthValue);
    setSavingId(idTecnico);
    setError(null);
    return bonoTecnicosApi
      .crearSolicitudAdmin(periodo, idTecnico, body)
      .then(cargar)
      .catch((err: unknown) => {
        console.error("Error al cargar la TV:", err);
        setError(err instanceof Error ? err.message : "No se pudo cargar la TV.");
        throw err;
      })
      .finally(() => setSavingId(null));
  };

  return {
    canUpdate,
    canApprove,
    monthValue,
    setMonthValue,
    filas,
    loading,
    savingId,
    savingSugeridos,
    error,
    guardarInput,
    cargarSugeridos,
    crearSolicitudTvAdmin,
  };
}
