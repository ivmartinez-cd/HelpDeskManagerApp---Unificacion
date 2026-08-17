"use client";

import { useMemo, useState } from "react";
import { cn } from "@/shared/utils/cn";
import type { Alerta, Incidente } from "../types/liquidaciones";
import { formatFecha } from "../lib/format";
import { IncidentesTabla } from "./incidentes-tabla";

export function IncidentesSeccion({
  titulo,
  accentClass,
  incidentes,
  alertasByInc,
  soloConAlertas,
}: {
  titulo: string;
  accentClass?: string;
  incidentes: Incidente[];
  alertasByInc: Record<string, Alerta[]>;
  soloConAlertas?: boolean;
}) {
  const [filtroFecha, setFiltroFecha] = useState("");

  const fechas = useMemo(
    () =>
      Array.from(
        new Set(incidentes.map((i) => i.fechaCierre).filter((f): f is string => !!f)),
      ).sort(),
    [incidentes],
  );

  const filtrados = useMemo(() => {
    const base = soloConAlertas
      ? incidentes.filter((i) => (alertasByInc[i.id] ?? []).length > 0)
      : incidentes;
    return filtroFecha ? base.filter((i) => i.fechaCierre === filtroFecha) : base;
  }, [incidentes, alertasByInc, soloConAlertas, filtroFecha]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 font-heading text-base font-bold text-foreground">
          {accentClass && <span className={cn("text-lg leading-none", accentClass)}>■</span>}
          {titulo}
          <span className="font-body text-sm font-normal text-muted-foreground">
            {incidentes.length.toLocaleString("es-AR")}
          </span>
        </h2>
        {fechas.length > 1 && (
          <label className="flex items-center gap-2 font-body text-xs text-muted-foreground">
            Filtrar por fecha de cierre:
            <select
              value={filtroFecha}
              onChange={(e) => setFiltroFecha(e.target.value)}
              className="rounded-[8px] border border-border bg-card px-2 py-1 font-body text-xs text-foreground outline-none focus:border-brand-orange/50"
            >
              <option value="">Todas</option>
              {fechas.map((f) => (
                <option key={f} value={f}>
                  {formatFecha(f)}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      <IncidentesTabla
        incidentes={filtrados}
        allIncidentes={incidentes}
        alertasByInc={alertasByInc}
      />
    </div>
  );
}
