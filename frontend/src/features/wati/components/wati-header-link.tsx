"use client";

import { MessageCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { turnosApi } from "@/features/turnos/api/turnos-api";
import type { ResolvedShift } from "@/features/turnos/types/turnos";

const REFRESH_MS = 5 * 60 * 1000;

function nowHHMMSS(now: Date): string {
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}:00`;
}

function dentroDeHorarioSt(shifts: ResolvedShift[], now: Date): boolean {
  const nowStr = nowHHMMSS(now);
  return shifts.some(
    (s) => s.casillaNombre === "ST" && s.horaInicio <= nowStr && nowStr < s.horaFin,
  );
}

/** Ícono fijo en el header, en TODA la app (no solo Inicio): recordatorio
 * para no olvidarse de revisar WATI durante el horario de Servicio
 * Técnico. Consulta los turnos reales de la casilla "ST" (mismos que la
 * card "Turnos del día") en vez de un rango de horario fijo en código, así
 * no se desactualiza si cambian las franjas. Si no existe una casilla "ST"
 * (o el fetch falla), el ícono simplemente nunca se destaca -- no rompe el
 * header. Sin URL configurada no se renderiza nada. */
export function WatiHeaderLink({ url }: { url: string | null }) {
  const [enHorario, setEnHorario] = useState(false);

  useEffect(() => {
    if (!url) return;
    let alive = true;
    const check = () => {
      turnosApi
        .getCurrentShifts()
        .then((r) => {
          if (alive) setEnHorario(dentroDeHorarioSt(r.shifts, new Date()));
        })
        .catch(() => {
          // best-effort -- ver docstring.
        });
    };
    check();
    const id = setInterval(check, REFRESH_MS);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [url]);

  if (!url) return null;

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      title={enHorario ? "WATI — revisar ahora" : "WATI"}
      className={
        enHorario
          ? "flex items-center gap-1.5 rounded-full border border-brand-orange bg-brand-orange/[0.12] px-2.5 py-1 font-heading text-[11px] font-bold text-brand-orange"
          : "flex items-center gap-1.5 rounded-[8px] p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
      }
    >
      <MessageCircle className="h-4 w-4" aria-hidden="true" />
      {enHorario && <span className="hidden sm:inline">Revisar ahora</span>}
    </a>
  );
}
