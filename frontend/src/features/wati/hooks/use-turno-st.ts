"use client";

import { useEffect, useState } from "react";
import { turnosApi } from "@/features/turnos/api/turnos-api";
import type { ResolvedShift } from "@/features/turnos/types/turnos";
import { enHorarioSt, esOperadorStEnTurno } from "../utils/turno-st";

const REFRESH_TURNOS_MS = 5 * 60 * 1000;
const TICK_MS = 60 * 1000;

export interface TurnoStState {
  /** Hay una franja de la casilla ST corriendo ahora. */
  enHorarioSt: boolean;
  /** El usuario logueado es quien cubre esa franja. */
  soyOperadorSt: boolean;
}

const INACTIVO: TurnoStState = { enHorarioSt: false, soyOperadorSt: false };

/** Turnos del día releídos cada 5 min y reevaluados cada minuto con la hora
 * local, así el cambio de turno se refleja sin esperar al próximo fetch.
 * Best-effort: si el fetch falla se queda con lo último que vio (o nada);
 * el ícono simplemente no se destaca y no se abre ningún aviso. */
export function useTurnoSt(activo: boolean, userId: string): TurnoStState {
  const [shifts, setShifts] = useState<ResolvedShift[]>([]);
  const [ahora, setAhora] = useState(() => Date.now());

  useEffect(() => {
    if (!activo) return;
    let alive = true;
    const cargar = () => {
      turnosApi
        .getCurrentShifts()
        .then((r) => {
          if (!alive) return;
          setShifts(r.shifts);
          setAhora(Date.now());
        })
        .catch((err: unknown) => {
          console.warn("No se pudieron leer los turnos del día para WATI:", err);
        });
    };
    cargar();
    const fetchId = setInterval(cargar, REFRESH_TURNOS_MS);
    const tickId = setInterval(() => setAhora(Date.now()), TICK_MS);
    return () => {
      alive = false;
      clearInterval(fetchId);
      clearInterval(tickId);
    };
  }, [activo]);

  if (!activo) return INACTIVO;
  const now = new Date(ahora);
  return {
    enHorarioSt: enHorarioSt(shifts, now),
    soyOperadorSt: esOperadorStEnTurno(shifts, userId, now),
  };
}
