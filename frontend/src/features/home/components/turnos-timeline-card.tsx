"use client";

import { CalendarClock, Clock } from "lucide-react";
import { useMemo } from "react";
import { TurnosTimeline, ejeHorario, type TimelineShift } from "@/features/turnos/components/turnos-timeline";
import { formatDiaMes } from "@/features/turnos/lib/variante-estado";
import type { ResolvedShift, VarianteActiva } from "@/features/turnos/types/turnos";
import { useNow } from "../hooks/use-now";
import { DashboardCard } from "./dashboard-card";
import { MiTurnoBanner } from "./mi-turno-banner";

export function TurnosTimelineCard({
  shifts,
  varianteActiva = null,
  loading,
  error,
  onRetry,
}: {
  shifts: ResolvedShift[];
  /** Grilla de vacaciones vigente hoy (ADR-025): badge en el header; el
   * timeline en sí no cambia, ya renderiza lo que `/current` resuelva. */
  varianteActiva?: VarianteActiva | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}) {
  // Línea "ahora" y badge, recalculados cada 30 s (comportamiento del handoff).
  const now = useNow(30_000);
  const timelineShifts = useMemo<TimelineShift[]>(
    () => shifts.map((s) => ({ ...s, key: s.slotId })),
    [shifts],
  );
  const { start, end } = ejeHorario(timelineShifts);
  const nowH = now.getHours() + now.getMinutes() / 60;
  const inHours = nowH >= start && nowH <= end;
  const hhmm = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;

  return (
    <DashboardCard
      icon={Clock}
      title="Turnos del día"
      subtitle={`Cobertura de operadores · ${String(start).padStart(2, "0")}:00 a ${String(end).padStart(2, "0")}:00`}
      loading={loading}
      error={error}
      onRetry={onRetry}
      headerRight={
        <div className="flex max-w-full flex-wrap items-center justify-end gap-1.5">
          <MiTurnoBanner shifts={shifts} loading={loading} />
          {varianteActiva && (
            <span
              title={varianteActiva.motivo ?? "Grilla de vacaciones"}
              className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-brand-orange/[0.13] px-2.5 py-1 font-heading text-[10.5px] font-bold text-brand-orange"
            >
              <CalendarClock className="h-3 w-3" />
              Grilla de vacaciones hasta el {formatDiaMes(varianteActiva.hasta)}
            </span>
          )}
          <span
            className={
              inHours
                ? "inline-flex shrink-0 items-center gap-1.5 rounded-full bg-success/[0.13] px-2.5 py-1 font-heading text-[10.5px] font-bold text-success"
                : "inline-flex shrink-0 items-center gap-1.5 rounded-full bg-muted px-2.5 py-1 font-heading text-[10.5px] font-bold text-muted-foreground"
            }
          >
            <span
              className={
                inHours ? "h-1.5 w-1.5 rounded-full bg-success" : "h-1.5 w-1.5 rounded-full bg-muted-foreground"
              }
            />
            {inHours ? `Ahora ${hhmm}` : `Fuera de horario · ${hhmm}`}
          </span>
        </div>
      }
    >
      <TurnosTimeline shifts={timelineShifts} nowH={nowH} />
    </DashboardCard>
  );
}
