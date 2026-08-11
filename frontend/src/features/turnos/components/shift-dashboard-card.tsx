"use client";

import { Clock, ShieldAlert, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { turnosApi } from "../api/turnos-api";
import type { ResolvedShift } from "../types/turnos";
import { Spinner } from "@/shared/components/ui/spinner";
import { contadoresApi } from "@/features/contadores/api/contadores-api";

interface CasillaGroup {
  casillaNombre: string;
  casillaColor?: string | null;
  allShifts: ResolvedShift[];
}

export function ShiftDashboardCard() {
  const [shifts, setShifts] = useState<ResolvedShift[]>([]);
  const [operatorColors, setOperatorColors] = useState<Map<string, string>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      turnosApi.getCurrentShifts(),
      contadoresApi.listCalendarioOperadores().catch(() => []),
    ])
      .then(([data, ops]) => {
        setShifts(data);
        const colorMap = new Map<string, string>();
        ops.forEach((op) => {
          if (op.color) colorMap.set(op.nombre.toLowerCase().trim(), op.color);
        });
        setOperatorColors(colorMap);
      })
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

  const getOpBadgeStyle = (userName: string, fallbackColor?: string | null) => {
    const key = userName.toLowerCase().trim();
    let hex = operatorColors.get(key);
    if (!hex) {
      const firstName = key.split(" ")[0];
      for (const [opName, opColor] of operatorColors.entries()) {
        if (opName.includes(firstName) || firstName.includes(opName.split(" ")[0])) {
          hex = opColor;
          break;
        }
      }
    }
    hex = hex || fallbackColor || "#3b82f6";
    return {
      backgroundColor: `${hex}20`,
      color: hex,
      borderColor: `${hex}40`,
    };
  };

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

          {/* Grilla completa de slots con resaltado AHORA/PRÓXIMO */}
          <div className="flex flex-col gap-1.5">
            {grp.allShifts.map((s) => (
              <div
                key={s.slotId}
                className={`flex items-center justify-between rounded-[8px] border px-3 py-2 transition-colors ${
                  s.isCurrent
                    ? "border-emerald-500/40 bg-emerald-500/10 shadow-xs"
                    : s.isNext
                    ? "border-amber-500/30 bg-amber-500/10"
                    : "border-border/60 bg-muted/20"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="font-body text-xs font-mono font-semibold text-foreground">
                    {s.horaInicio.slice(0, 5)} - {s.horaFin.slice(0, 5)}
                  </span>
                  {s.isCurrent && (
                    <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 font-body text-[10px] font-extrabold text-emerald-600 dark:text-emerald-400">
                      AHORA
                    </span>
                  )}
                  {s.isNext && (
                    <span className="rounded-full bg-amber-500/20 px-2 py-0.5 font-body text-[10px] font-extrabold text-amber-600 dark:text-amber-400">
                      PRÓXIMO
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap gap-1.5 justify-end">
                  {s.operadores.length > 0 ? (
                    s.operadores.map((op) => (
                      <span
                        key={op.userId}
                        style={getOpBadgeStyle(op.userName, grp.casillaColor)}
                        className="rounded-full border px-2.5 py-0.5 font-body text-xs font-semibold"
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
