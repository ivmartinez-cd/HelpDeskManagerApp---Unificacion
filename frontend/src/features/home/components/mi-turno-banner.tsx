"use client";

import { CalendarClock } from "lucide-react";
import { useSession } from "@/services/session-provider";
import type { ResolvedShift } from "@/features/turnos/types/turnos";
import { useNow } from "../hooks/use-now";

function nowHHMMSS(now: Date): string {
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}:00`;
}

function formatRango(shift: ResolvedShift): string {
  return `${shift.horaInicio.slice(0, 5)}–${shift.horaFin.slice(0, 5)}`;
}

/** Leyenda personal de turno: cruza el usuario logueado contra los turnos
 * de HOY (sin fetch propio). Si hay una franja propia en curso dice "Ahora
 * estás en:" con esa casilla primero; si no, "Hoy te toca:". Sin turno propio
 * no renderiza nada — es un aviso personal, el resumen del equipo es la card.
 * Vive en el header de "Turnos del día" (rediseño 2026-08-22), como chips. */
export function MiTurnoBanner({
  shifts,
  loading,
}: {
  shifts: ResolvedShift[];
  loading: boolean;
}) {
  const { user } = useSession();
  const now = useNow(30_000);

  if (loading || !now) return null;
  const propios = shifts.filter((s) => s.operadores.some((o) => o.userId === user.id));
  if (propios.length === 0) return null;

  const nowStr = nowHHMMSS(now);
  const enCurso = (s: ResolvedShift) => s.horaInicio <= nowStr && nowStr < s.horaFin;
  const actual = propios.find(enCurso);
  const ordenados = actual ? [actual, ...propios.filter((s) => s !== actual)] : propios;

  return (
    <div className="inline-flex max-w-full flex-wrap items-center gap-1.5">
      <CalendarClock className="h-3.5 w-3.5 shrink-0 text-brand-orange" aria-hidden="true" />
      <span className="font-body text-[12px] font-semibold text-foreground">
        {actual ? "Ahora estás en:" : "Hoy te toca:"}
      </span>
      {ordenados.map((shift) => (
        <span
          key={shift.slotId}
          className={
            shift === actual
              ? "inline-flex items-center rounded-full bg-accent px-2 py-0.5 font-heading text-[10.5px] font-bold text-accent-foreground"
              : "inline-flex items-center rounded-full bg-brand-orange/[0.15] px-2 py-0.5 font-heading text-[10.5px] font-bold text-brand-orange"
          }
        >
          {shift.casillaNombre} {formatRango(shift)}
        </span>
      ))}
    </div>
  );
}
