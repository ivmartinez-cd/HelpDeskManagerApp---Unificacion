"use client";

import { Tooltip } from "@/shared/components/ui/tooltip";
import {
  buildGridDays,
  eventosDelDia,
  feriadoDelDia,
  WEEKDAY_LABELS,
} from "../lib/calendario";
import type { EventoCalendario } from "../types/vacaciones";

const MAX_PILLS = 2;

interface Props {
  year: number;
  month: number; // 1-12
  hoyIso: string;
  eventos: EventoCalendario[];
}

export function VacacionesMonthGrid({ year, month, hoyIso, eventos }: Props) {
  const celdas = buildGridDays(year, month, hoyIso);

  return (
    <div className="overflow-hidden rounded-[12px] border border-border">
      <div className="grid grid-cols-7 border-b border-border bg-muted/30">
        {WEEKDAY_LABELS.map((d) => (
          <div
            key={d}
            className="px-2 py-2 text-center font-heading text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground"
          >
            {d}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {celdas.map((celda) => {
          const delDia = eventosDelDia(eventos, celda.iso);
          const feriado = feriadoDelDia(eventos, celda.iso);
          const extras = delDia.length - MAX_PILLS;
          return (
            <div
              key={celda.iso}
              className={`min-h-[86px] border-b border-r border-border/60 p-1.5 [&:nth-child(7n)]:border-r-0 ${
                celda.isWeekend || !celda.inMonth ? "bg-muted/20" : "bg-card"
              }`}
            >
              <div className="mb-1 flex items-center justify-between">
                <span
                  className={
                    celda.isToday
                      ? "flex h-6 w-6 items-center justify-center rounded-full bg-brand-orange font-body text-xs font-bold text-white"
                      : `font-body text-xs ${celda.inMonth ? "text-foreground" : "text-muted-foreground/50"}`
                  }
                >
                  {celda.day}
                </span>
                {feriado && (
                  <Tooltip content={feriado.title}>
                    <span className="h-2 w-2 rounded-full bg-red-500" />
                  </Tooltip>
                )}
              </div>
              <div className="flex flex-col gap-0.5">
                {delDia.slice(0, MAX_PILLS).map((e) => (
                  <Tooltip key={e.id} content={e.title}>
                    <span
                      className="block truncate rounded-[4px] px-1.5 py-0.5 font-body text-[10px] font-semibold text-white"
                      style={{
                        backgroundColor: e.color,
                        borderLeft: e.borderColor
                          ? `3px solid ${e.borderColor}`
                          : undefined,
                        opacity: e.status === "PENDING" ? 0.55 : 1,
                      }}
                    >
                      {e.empleado ?? e.title}
                    </span>
                  </Tooltip>
                ))}
                {extras > 0 && (
                  <span className="px-1 font-body text-[10px] text-muted-foreground">
                    +{extras} más
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
