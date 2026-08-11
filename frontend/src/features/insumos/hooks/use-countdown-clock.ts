"use client";

import { useEffect, useState } from "react";

/** Reloj compartido de 1 segundo para los countdown de "Validando".
 *
 * Port de `useValidationCountdown.ts` del legacy, que declaraba el `ref` a
 * nivel de módulo para que TODAS las filas compartieran un solo `setInterval`.
 * Acá no hace falta estado de módulo ni Context: el countdown solo lo usa la
 * tabla del Dashboard, así que se instancia UNA vez en el componente que
 * renderiza las filas y el valor baja por props. Un `setInterval` para toda la
 * tabla, igual que el legacy.
 *
 * `enabled` corta el intervalo cuando no hay ninguna fila en validación — sin
 * eso la pantalla re-renderiza una vez por segundo para siempre sin motivo.
 */
export function useCountdownClock(enabled: boolean): number {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!enabled) return;
    const handle = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(handle);
  }, [enabled]);

  return now;
}

/** `MM:SS` restantes hasta `deadlineIso`, nunca negativo. Igual que el legacy. */
export function formatCountdown(deadlineIso: string | null | undefined, nowMs: number): string {
  if (!deadlineIso) return "—";
  const deadlineMs = new Date(deadlineIso).getTime();
  if (Number.isNaN(deadlineMs)) return "—";
  const totalSeconds = Math.ceil(Math.max(0, deadlineMs - nowMs) / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

/** `true` si la ventana de validación de la fila ya venció contra `nowMs`. */
export function isCountdownExpired(deadlineIso: string | null | undefined, nowMs: number): boolean {
  if (!deadlineIso) return false;
  const deadlineMs = new Date(deadlineIso).getTime();
  return !Number.isNaN(deadlineMs) && deadlineMs <= nowMs;
}
