"use client";

import Link from "next/link";
import { CalendarClock, X } from "lucide-react";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { formatFecha } from "../lib/fechas";
import type { DecisionResult } from "../types/vacaciones";
import type { AvisoTurnos } from "./novedades-aprobacion";

/** Aviso de vacaciones aprobadas con impacto en turnos + link al editor del
 * modo vacaciones de turnos (ADR-025), extraído de `aprobaciones-view.tsx`
 * porque ese archivo ya superaba el tamaño máximo de archivo (§4). */
export function avisoDeVacaciones(decision: DecisionResult): AvisoTurnos | null {
  if (!decision.afectaTurnos) return null;
  return {
    empleadoNombre: decision.empleadoNombre,
    startDate: decision.startDate,
    endDate: decision.endDate,
    afectaTurnos: decision.afectaTurnos,
    motivo: `Vacaciones ${decision.empleadoNombre}`,
  };
}

export function hrefArmarGrillaCobertura(decision: AvisoTurnos): string {
  const q = new URLSearchParams({
    tab: "vacaciones",
    ausente: decision.afectaTurnos.userId,
    desde: decision.startDate,
    hasta: decision.endDate,
    motivo: decision.motivo,
  });
  return `/turnos?${q.toString()}`;
}

export function AvisoAfectaTurnos({
  decision,
  onClose,
}: {
  decision: AvisoTurnos;
  onClose: () => void;
}) {
  return (
    <div
      role="status"
      className="flex flex-wrap items-center justify-between gap-4 rounded-[12px] border border-brand-orange/20 bg-brand-orange/10 px-5 py-4"
    >
      <div className="flex items-start gap-3">
        <CalendarClock className="mt-0.5 h-5 w-5 shrink-0 text-brand-orange" />
        <div className="flex flex-col gap-0.5">
          <p className="font-body text-sm font-semibold text-foreground">
            {decision.empleadoNombre} tiene turnos de casilla entre el{" "}
            {formatFecha(decision.startDate)} y el {formatFecha(decision.endDate)}.
          </p>
          <p className="font-body text-xs text-muted-foreground">
            La aprobación quedó registrada. La grilla de cobertura no se arma sola: re-cortar
            franjas exige criterio humano. Podés armarla ahora en el Modo vacaciones de Turnos.
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Link
          href={hrefArmarGrillaCobertura(decision)}
          className={brandButtonClasses({ size: "sm" })}
        >
          Armar grilla de cobertura →
        </Link>
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar aviso de turnos"
          className="rounded-[8px] p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
