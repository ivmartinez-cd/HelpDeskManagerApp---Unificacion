"use client";

import { Clock, ShieldAlert, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { turnosApi } from "../api/turnos-api";
import type { ResolvedShift } from "../types/turnos";
import { Spinner } from "@/shared/components/ui/spinner";
import { cn } from "@/shared/utils/cn";

interface CasillaGroup {
  casillaNombre: string;
  casillaColor?: string | null;
  allShifts: ResolvedShift[];
}

export function ShiftDashboardCard() {
  const [shifts, setShifts] = useState<ResolvedShift[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    turnosApi
      .getCurrentShifts()
      .then(setShifts)
      .catch((err: unknown) => {
        console.error("Error al cargar turnos de casillas:", err);
        setError("No se pudo cargar la distribución de casillas.");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex w-full max-w-sm items-center justify-center rounded-[12px] border border-border bg-card p-6 min-h-[160px]">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex w-full max-w-sm items-center gap-3 rounded-[12px] border border-destructive/20 bg-destructive/5 p-5 text-destructive">
        <ShieldAlert className="h-5 w-5 shrink-0" />
        <span className="font-body text-sm">{error}</span>
      </div>
    );
  }

  if (shifts.length === 0) {
    return (
      <div className="flex w-full max-w-sm flex-col gap-3 rounded-[12px] border border-border bg-card p-5">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-[9px] bg-brand-orange/[0.12] text-brand-orange">
            <Users className="h-4 w-4" />
          </span>
          <div className="flex flex-col">
            <h2 className="font-heading text-[14.5px] font-bold text-foreground">
              Turnos en Casillas
            </h2>
            <span className="font-body text-[12.5px] text-muted-foreground">
              Distribución de operadores
            </span>
          </div>
        </div>
        <p className="font-body text-xs text-muted-foreground py-2">
          No hay horarios configurados para el día de hoy.
        </p>
      </div>
    );
  }

  // Group shifts by Casilla and sort slots chronologically
  const grouped = new Map<string, CasillaGroup>();
  shifts.forEach((shift) => {
    if (!grouped.has(shift.casillaNombre)) {
      grouped.set(shift.casillaNombre, {
        casillaNombre: shift.casillaNombre,
        casillaColor: shift.casillaColor,
        allShifts: [],
      });
    }
    grouped.get(shift.casillaNombre)!.allShifts.push(shift);
  });

  const groups = Array.from(grouped.values()).map((grp) => ({
    ...grp,
    allShifts: grp.allShifts.sort((a, b) => a.horaInicio.localeCompare(b.horaInicio)),
  }));

  return (
    <>
      {groups.map((grp) => (
        <div
          key={grp.casillaNombre}
          className="flex w-full max-w-sm flex-col gap-3 rounded-[12px] border border-border bg-card p-5"
        >
          {/* Header de Casilla */}
          <div className="flex items-center gap-2.5 border-b border-border/60 pb-2.5">
            <span
              style={
                grp.casillaColor
                  ? { backgroundColor: `${grp.casillaColor}20`, color: grp.casillaColor }
                  : undefined
              }
              className="flex h-9 w-9 items-center justify-center rounded-[9px] bg-brand-orange/[0.12] text-brand-orange"
            >
              <Clock className="h-4 w-4" />
            </span>
            <div className="flex flex-col">
              <h2 className="font-heading text-[14.5px] font-bold text-foreground tracking-wide uppercase">
                Turnos {grp.casillaNombre}
              </h2>
              <span className="font-body text-[12.5px] text-muted-foreground">
                Distribución del día
              </span>
            </div>
          </div>

          {/* Lista de slots con resaltado AHORA/PRÓXIMO — filas separadas por
              línea, sin caja por operador. El nombre va en el color real de
              Gestión (AppUser.color, ver ADR-009), no naranja/gris por
              estado (feedback del usuario del 2026-08-12). */}
          <div className="flex flex-col divide-y divide-border/50">
            {grp.allShifts.map((s) => (
              <div key={s.slotId} className="flex items-center justify-between gap-3 py-2.5">
                <div className="flex items-center gap-2">
                  <span className="font-body text-xs font-mono font-semibold text-foreground">
                    {s.horaInicio.slice(0, 5)} – {s.horaFin.slice(0, 5)}
                  </span>
                  {s.isCurrent && (
                    <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 font-body text-[10px] font-extrabold text-emerald-600 dark:text-emerald-400">
                      AHORA
                    </span>
                  )}
                  {s.isNext && (
                    <span className="rounded-full bg-brand-orange/15 px-2 py-0.5 font-body text-[10px] font-extrabold text-brand-orange">
                      PRÓXIMO
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap justify-end gap-x-2">
                  {s.operadores.length > 0 ? (
                    s.operadores.map((op) => (
                      <span
                        key={op.userId}
                        style={op.color ? { color: op.color } : undefined}
                        className={cn(
                          "font-body text-[13px] font-bold",
                          !op.color && "text-muted-foreground",
                        )}
                      >
                        {op.userName}
                      </span>
                    ))
                  ) : (
                    <span className="font-body text-xs italic text-muted-foreground">
                      Sin asignar
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </>
  );
}
