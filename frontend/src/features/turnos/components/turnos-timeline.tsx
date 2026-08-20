"use client";

import { useMemo } from "react";
import { FALLBACK_COLOR, accentText, tint } from "@/features/home/utils/inicio-format";
import type { OperatorShift } from "../types/turnos";

/** Franja a dibujar: lo mínimo común entre `ResolvedShift` (/current) y una
 * franja de grilla variante. */
export interface TimelineShift {
  key: string;
  casillaNombre: string;
  /** HH:MM o HH:MM:SS */
  horaInicio: string;
  horaFin: string;
  operadores: OperatorShift[];
}

function toHours(hhmm: string): number {
  const [h, m] = hhmm.split(":").map(Number);
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
  /** Solo nombres de pila, para franjas angostas ("Victor" en vez de "Victor Paez"). */
  labelCorto: string;
  tip: string;
}

/** Debajo de este ancho (% del eje) el nombre completo no entra: se muestra
 * el nombre de pila y el rango en tipografía más chica; el tooltip conserva
 * todo. Una franja de 1 h sobre el eje 08–18 es el 10 %. */
const ANCHO_ANGOSTO_PCT = 14;

interface Track {
  name: string;
  segs: Segmento[];
}

/** Eje del timeline: 08–18 del handoff, extendido si algún turno real se sale. */
export function ejeHorario(shifts: TimelineShift[]): { start: number; end: number } {
  let start = 8;
  let end = 18;
  for (const s of shifts) {
    start = Math.min(start, Math.floor(toHours(s.horaInicio)));
    end = Math.max(end, Math.ceil(toHours(s.horaFin)));
  }
  return { start, end };
}

function fmtHora(h: number): string {
  const entera = Math.floor(h);
  const min = Math.round((h - entera) * 60);
  return min === 0 ? `${entera}` : `${entera}:${String(min).padStart(2, "0")}`;
}

function buildTracks(
  shifts: TimelineShift[],
  start: number,
  span: number,
  ordenCasillas?: string[],
): Track[] {
  const porCasilla = new Map<string, TimelineShift[]>();
  for (const nombre of ordenCasillas ?? []) porCasilla.set(nombre, []);
  for (const s of shifts) {
    const grupo = porCasilla.get(s.casillaNombre) ?? [];
    grupo.push(s);
    porCasilla.set(s.casillaNombre, grupo);
  }
  return Array.from(porCasilla.entries())
    .filter(([, grupo]) => grupo.length > 0)
    .map(([name, grupo]) => ({
      name: `Turnos ${name}`,
      segs: grupo
        .sort((a, b) => a.horaInicio.localeCompare(b.horaInicio))
        .map((s) => {
          const desde = toHours(s.horaInicio);
          const hasta = toHours(s.horaFin);
          const color = s.operadores[0]?.color ?? FALLBACK_COLOR;
          const nombres = s.operadores.map((o) => o.userName).join(" · ") || "Sin asignar";
          const nombresCortos =
            s.operadores.map((o) => o.userName.trim().split(/\s+/)[0]).join(" · ") || "Sin asignar";
          const widthPct = ((hasta - desde) / span) * 100;
          return {
            key: s.key,
            left: `${((desde - start) / span) * 100}%`,
            width: `${widthPct}%`,
            widthPct,
            color,
            bg: tint(color),
            range: `${fmtHora(desde)}–${fmtHora(hasta)}h`,
            label: nombres,
            labelCorto: nombresCortos,
            tip: `${nombres} · ${s.horaInicio.slice(0, 5)}–${s.horaFin.slice(0, 5)}`,
          };
        }),
    }));
}

interface TurnosTimelineProps {
  shifts: TimelineShift[];
  /** Hora decimal de "ahora" para la línea vertical; omitir = sin línea. */
  nowH?: number | null;
  /** Orden de los tracks (nombres de casilla); default: orden de aparición. */
  ordenCasillas?: string[];
  emptyText?: string;
}

/** Timeline de turnos del handoff de Inicio (tracks por casilla, eje horario,
 * leyenda de operadores). Lo usan la card "Turnos del día" y la vista previa
 * de una grilla de vacaciones (ADR-025) — mismo dibujo, para que lo que se
 * comparte con los operadores sea exactamente lo que después ven en Inicio. */
export function TurnosTimeline({
  shifts,
  nowH = null,
  ordenCasillas,
  emptyText = "No hay horarios configurados para el día de hoy.",
}: TurnosTimelineProps) {
  const { start, end } = ejeHorario(shifts);
  const span = end - start;
  const tracks = useMemo(
    () => buildTracks(shifts, start, span, ordenCasillas),
    [shifts, start, span, ordenCasillas],
  );

  const operadores = new Map<string, { name: string; color: string }>();
  for (const s of shifts) {
    for (const op of s.operadores) {
      operadores.set(op.userId, { name: op.userName, color: op.color ?? FALLBACK_COLOR });
    }
  }
  const inHours = nowH !== null && nowH >= start && nowH <= end;
  const ticks = Array.from({ length: Math.floor(span / 2) + 1 }, (_, i) => start + i * 2);

  if (shifts.length === 0) {
    return <p className="pt-3 font-body text-[13px] text-muted-foreground">{emptyText}</p>;
  }

  return (
    <div className="flex flex-col pt-3">
      {tracks.map((track) => (
        <div key={track.name} className="mb-3">
          <div className="mb-1.5 font-heading text-[10.5px] font-bold uppercase tracking-[.06em] text-muted-foreground">
            {track.name}
          </div>
          <div className="relative h-[46px] overflow-hidden rounded-[9px] bg-white/[.03]">
            {track.segs.map((seg) => {
              const angosta = seg.widthPct < ANCHO_ANGOSTO_PCT;
              return (
                <div
                  key={seg.key}
                  title={seg.tip}
                  className={`absolute inset-y-0 flex flex-col justify-center overflow-hidden border-r-2 border-card ${
                    angosta ? "px-1" : "px-2"
                  }`}
                  style={{ left: seg.left, width: seg.width, background: seg.bg }}
                >
                  <span
                    className={`truncate font-heading font-bold ${angosta ? "text-[9px]" : "text-[10px]"}`}
                    style={{ color: accentText(seg.color) }}
                  >
                    {seg.range}
                  </span>
                  <span
                    className={`truncate font-body font-semibold text-foreground ${
                      angosta ? "text-[10.5px]" : "text-[11.5px]"
                    }`}
                  >
                    {angosta ? seg.labelCorto : seg.label}
                  </span>
                </div>
              );
            })}
            {inHours && nowH !== null && (
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
            <span className="font-body text-[12px] font-semibold text-muted-foreground">{op.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
