"use client";

import { Clock } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { ResolvedShift } from "@/features/turnos/types/turnos";
import { FALLBACK_COLOR, accentText, tint } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";

function toHours(hhmmss: string): number {
  const [h, m] = hhmmss.split(":").map(Number);
  return h + (m || 0) / 60;
}

interface Segmento {
  key: string;
  left: string;
  width: string;
  widthPct: number;
  color: string;
  bg: string;
  range: string;
  label: string;
  tip: string;
}

interface Track {
  name: string;
  segs: Segmento[];
}

/** Eje del timeline: 08–18 del handoff, extendido si algún turno real se sale. */
function ejeHorario(shifts: ResolvedShift[]): { start: number; end: number } {
  let start = 8;
  let end = 18;
  for (const s of shifts) {
    start = Math.min(start, Math.floor(toHours(s.horaInicio)));
    end = Math.max(end, Math.ceil(toHours(s.horaFin)));
  }
  return { start, end };
}

function buildTracks(shifts: ResolvedShift[], start: number, span: number): Track[] {
  const porCasilla = new Map<string, ResolvedShift[]>();
  for (const s of shifts) {
    const grupo = porCasilla.get(s.casillaNombre) ?? [];
    grupo.push(s);
    porCasilla.set(s.casillaNombre, grupo);
  }
  return Array.from(porCasilla.entries()).map(([name, grupo]) => ({
    name: `Turnos ${name}`,
    segs: grupo
      .sort((a, b) => a.horaInicio.localeCompare(b.horaInicio))
      .map((s) => {
        const desde = toHours(s.horaInicio);
        const hasta = toHours(s.horaFin);
        const color = s.operadores[0]?.color ?? FALLBACK_COLOR;
        const nombres = s.operadores.map((o) => o.userName).join(" · ") || "Sin asignar";
        const widthPct = ((hasta - desde) / span) * 100;
        return {
          key: s.slotId,
          left: `${((desde - start) / span) * 100}%`,
          width: `${widthPct}%`,
          widthPct,
          color,
          bg: tint(color),
          range: `${Math.round(desde)}–${Math.round(hasta)}h`,
          label: nombres,
          tip: `${nombres} · ${s.horaInicio.slice(0, 5)}–${s.horaFin.slice(0, 5)}`,
        };
      }),
  }));
}

export function TurnosTimelineCard({
  shifts,
  loading,
  error,
}: {
  shifts: ResolvedShift[];
  loading: boolean;
  error: string | null;
}) {
  // Línea "ahora" y badge, recalculados cada 30 s (comportamiento del handoff).
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 30_000);
    return () => clearInterval(id);
  }, []);

  const { start, end } = ejeHorario(shifts);
  const span = end - start;
  const tracks = useMemo(() => buildTracks(shifts, start, span), [shifts, start, span]);

  const operadores = new Map<string, { name: string; color: string }>();
  for (const s of shifts) {
    for (const op of s.operadores) {
      operadores.set(op.userId, { name: op.userName, color: op.color ?? FALLBACK_COLOR });
    }
  }

  const nowH = now.getHours() + now.getMinutes() / 60;
  const inHours = nowH >= start && nowH <= end;
  const hhmm = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
  const ticks = Array.from({ length: Math.floor(span / 2) + 1 }, (_, i) => start + i * 2);

  return (
    <DashboardCard
      icon={Clock}
      title="Turnos del día"
      subtitle={`Cobertura de operadores · ${String(start).padStart(2, "0")}:00 a ${String(end).padStart(2, "0")}:00`}
      loading={loading}
      error={error}
      headerRight={
        <span
          className={
            inHours
              ? "inline-flex shrink-0 items-center gap-1.5 rounded-full bg-emerald-500/[0.13] px-2.5 py-1 font-heading text-[10.5px] font-bold text-emerald-500"
              : "inline-flex shrink-0 items-center gap-1.5 rounded-full bg-muted px-2.5 py-1 font-heading text-[10.5px] font-bold text-muted-foreground"
          }
        >
          <span
            className={
              inHours ? "h-1.5 w-1.5 rounded-full bg-emerald-500" : "h-1.5 w-1.5 rounded-full bg-muted-foreground"
            }
          />
          {inHours ? `Ahora ${hhmm}` : `Fuera de horario · ${hhmm}`}
        </span>
      }
    >
      {shifts.length === 0 ? (
        <p className="pt-3 font-body text-[13px] text-muted-foreground">
          No hay horarios configurados para el día de hoy.
        </p>
      ) : (
        <div className="flex flex-col pt-3">
          {tracks.map((track) => (
            <div key={track.name} className="mb-3">
              <div className="mb-1.5 font-heading text-[10.5px] font-bold uppercase tracking-[.06em] text-muted-foreground">
                {track.name}
              </div>
              <div className="relative h-[46px] overflow-hidden rounded-[9px] bg-white/[.03]">
                {track.segs.map((seg) => (
                  <div
                    key={seg.key}
                    title={seg.tip}
                    className="absolute inset-y-0 flex flex-col justify-center overflow-hidden border-r-2 border-card px-2"
                    style={{ left: seg.left, width: seg.width, background: seg.bg }}
                  >
                    {seg.widthPct >= 12 && (
                      <span
                        className="truncate font-heading text-[10px] font-bold"
                        style={{ color: accentText(seg.color) }}
                      >
                        {seg.range}
                      </span>
                    )}
                    <span className="truncate font-body text-[11.5px] font-semibold text-foreground">
                      {seg.label}
                    </span>
                  </div>
                ))}
                {inHours && (
                  <div
                    className="absolute -inset-y-0.5 w-0.5 bg-white shadow-[0_0_8px_rgba(255,255,255,.6)]"
                    style={{ left: `${((nowH - start) / span) * 100}%` }}
                  />
                )}
              </div>
            </div>
          ))}
          <div className="flex justify-between px-0.5">
            {ticks.map((h) => (
              <span key={h} className="font-body text-[10.5px] font-semibold text-muted-foreground">
                {String(h).padStart(2, "0")}:00
              </span>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-x-3.5 gap-y-1.5 border-t border-border/60 pt-3">
            {Array.from(operadores.values()).map((op) => (
              <div key={op.name} className="flex items-center gap-1.5">
                <span className="h-[9px] w-[9px] rounded-[3px]" style={{ background: op.color }} />
                <span className="font-body text-[12px] font-semibold text-muted-foreground">
                  {op.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </DashboardCard>
  );
}
