"use client";

import { useMemo, useState } from "react";
import { cn } from "@/shared/utils/cn";
import { useSeleccionAlertas } from "../hooks/seleccion-alertas-context";
import type { Alerta, Incidente, PrestadorLiquidacion } from "../types/liquidaciones";
import { formatFechaDia } from "../lib/format";
import { IncidentesTabla } from "./incidentes-tabla";

export function IncidentesSeccion({
  liquidacionId,
  prestadorId,
  prestadores,
  titulo,
  accentClass,
  incidentes,
  incidentesById,
  alertasByInc,
  soloConAlertas,
  onAlertaChanged,
}: {
  liquidacionId: string;
  prestadorId: string;
  prestadores: PrestadorLiquidacion[];
  titulo: string;
  accentClass?: string;
  incidentes: Incidente[];
  incidentesById: Record<string, Incidente>;
  alertasByInc: Record<string, Alerta[]>;
  soloConAlertas?: boolean;
  onAlertaChanged: () => void;
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

  // "Tildar todos": los incidentes visibles (respeta el filtro de fecha) con
  // alertas abiertas, para gestionarlas en lote desde la barra flotante.
  const seleccion = useSeleccionAlertas();
  const seleccionables = useMemo(
    () => (seleccion ? filtrados.filter((i) => seleccion.esSeleccionable(i.id)) : []),
    [filtrados, seleccion],
  );
  const todosTildados =
    seleccionables.length > 0 && seleccionables.every((i) => seleccion?.seleccionados.has(i.id));

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
        {seleccion && seleccionables.length > 0 && (
          <label className="flex items-center gap-2 font-body text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={todosTildados}
              onChange={(e) =>
                seleccion.seleccionarTodos(seleccionables.map((i) => i.id), e.target.checked)
              }
              className="h-3.5 w-3.5 accent-brand-orange"
            />
            Tildar los {seleccionables.length} con alertas abiertas
          </label>
        )}
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
                  {formatFechaDia(f)}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      <IncidentesTabla
        liquidacionId={liquidacionId}
        prestadorId={prestadorId}
        prestadores={prestadores}
        incidentes={filtrados}
        allIncidentes={incidentes}
        incidentesById={incidentesById}
        alertasByInc={alertasByInc}
        onAlertaChanged={onAlertaChanged}
      />
    </div>
  );
}
