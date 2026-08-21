"use client";

import { CalendarClock } from "lucide-react";
import { useEffect, useState } from "react";
import { useSession } from "@/services/session-provider";
import type { ResolvedShift } from "@/features/turnos/types/turnos";

function nowHHMMSS(now: Date): string {
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}:00`;
}

function formatRango(shift: ResolvedShift): string {
  return `${shift.horaInicio.slice(0, 5)}–${shift.horaFin.slice(0, 5)}`;
}

/** Leyenda personal de turno vinculada al login: cruza el usuario logueado
 * contra los turnos de HOY que ya trae `useTurnosHoy()` (sin fetch propio).
 * Si hay una franja propia en curso dice "Ahora estás en:" con esa casilla
 * primero y el resto del día después, atenuado; si ninguna está en curso
 * (antes de empezar, entre franjas, al terminar) dice "Hoy te toca:" con
 * todas. Si el usuario no tiene ningún turno hoy, no se renderiza nada -- es
 * un aviso personal, no un resumen del equipo (para eso ya está la card
 * "Turnos del día"). Se ubica a la derecha del título de Inicio (pedido del
 * usuario, 2026-08-21). */
export function MiTurnoBanner({
  shifts,
  loading,
}: {
  shifts: ResolvedShift[];
  loading: boolean;
}) {
  const { user } = useSession();
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 30_000);
    return () => clearInterval(id);
  }, []);

  if (loading) return null;
  const propios = shifts.filter((s) => s.operadores.some((o) => o.userId === user.id));
  if (propios.length === 0) return null;

  const nowStr = nowHHMMSS(now);
  const enCurso = (s: ResolvedShift) => s.horaInicio <= nowStr && nowStr < s.horaFin;
  const actual = propios.find(enCurso);
  // La franja en curso va primero; el resto del día queda como contexto.
  const ordenados = actual ? [actual, ...propios.filter((s) => s !== actual)] : propios;

  return (
    <div className="inline-flex max-w-full flex-wrap items-center justify-end gap-2 rounded-[12px] border border-brand-orange/30 bg-brand-orange/[0.08] px-4 py-2.5">
      <CalendarClock className="h-4 w-4 shrink-0 text-brand-orange" />
      <span className="font-body text-[13px] font-semibold text-foreground">
        {actual ? "Ahora estás en:" : "Hoy te toca:"}
      </span>
      <div className="flex flex-wrap items-center gap-2">
        {ordenados.map((shift) => (
          <span
            key={shift.slotId}
            className={
              shift === actual
                ? "inline-flex items-center gap-1 rounded-full bg-accent px-2.5 py-0.5 font-heading text-[11px] font-bold text-accent-foreground"
                : "inline-flex items-center gap-1 rounded-full bg-brand-orange/[0.15] px-2.5 py-0.5 font-heading text-[11px] font-bold text-brand-orange"
            }
          >
            {shift.casillaNombre} {formatRango(shift)}
          </span>
        ))}
      </div>
    </div>
  );
}
