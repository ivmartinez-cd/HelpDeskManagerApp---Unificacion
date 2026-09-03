"use client";

import { useMemo, useState } from "react";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";
import type { Alerta, Incidente, PrestadorLiquidacion } from "../types/liquidaciones";
import { formatARS } from "../lib/format";
import { computeRutasCompartidas } from "../lib/rutas-compartidas";
import { IncidenteRow } from "./incidente-row";

type IncSortKey =
  | "incidente"
  | "serie"
  | "empresa"
  | "tipo"
  | "kmCobrado"
  | "kmEsperado"
  | "cobrado"
  | "esperado"
  | "diferencia"
  | "fecha";

const INC_SORT_KEYS: readonly IncSortKey[] = [
  "incidente", "serie", "empresa", "tipo",
  "kmCobrado", "kmEsperado", "cobrado", "esperado", "diferencia", "fecha",
];

export function IncidentesTabla({
  liquidacionId,
  prestadorId,
  prestadores,
  incidentes,
  allIncidentes,
  incidentesById,
  alertasByInc,
  onAlertaChanged,
}: {
  liquidacionId: string;
  prestadorId: string;
  prestadores: PrestadorLiquidacion[];
  incidentes: Incidente[];
  allIncidentes: Incidente[];
  incidentesById: Record<string, Incidente>;
  alertasByInc: Record<string, Alerta[]>;
  onAlertaChanged: () => void;
}) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const { sort, toggleSort } = useTableSort<IncSortKey>({
    initial: { key: "incidente", direction: "asc" },
    keys: INC_SORT_KEYS,
    descFirstKeys: ["kmCobrado", "kmEsperado", "cobrado", "esperado", "diferencia", "fecha"],
  });

  const rutasCompartidas = useMemo(() => computeRutasCompartidas(allIncidentes), [allIncidentes]);

  const sorted = useMemo(() => {
    return [...incidentes].sort((a, b) => {
      const getSv = (inc: Incidente) => {
        switch (sort.key) {
          case "incidente": return inc.numeroIncidente;
          case "serie": return inc.nroSerie ?? null;
          case "empresa":
            return [inc.empresaNombre, inc.sucursalNombre].filter(Boolean).join(" / ") || null;
          case "tipo": return inc.tipo;
          case "kmCobrado": return inc.cantKmCobrado;
          case "kmEsperado": return inc.cantKmEsperado;
          case "cobrado": return inc.costoServicioCobrado;
          case "esperado": return inc.costoServicioEsperado;
          case "diferencia":
            return inc.costoServicioEsperado !== null
              ? inc.costoServicioCobrado - inc.costoServicioEsperado
              : null;
          case "fecha": return inc.fechaCierre ?? null;
        }
      };
      return compareSortValues(getSv(a), getSv(b), sort.direction);
    });
  }, [incidentes, sort]);

  const toggleExpanded = (incId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(incId)) next.delete(incId);
      else next.add(incId);
      return next;
    });
  };

  const totalKms = incidentes.reduce((s, i) => s + i.cantKmCobrado, 0);
  const totalServicio = incidentes.reduce((s, i) => s + i.costoServicioCobrado, 0);
  const totalGeneral = incidentes.reduce((s, i) => s + i.costoTotalCobrado, 0);

  const thCls =
    "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";

  if (incidentes.length === 0) {
    return (
      <div className="overflow-hidden rounded-[12px] border border-border bg-card">
        <p className="px-4 py-6 font-body text-sm text-muted-foreground">Sin incidentes.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-muted/40">
              <SortableHeader column={{ key: "incidente", label: "Nro Incidente" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "serie", label: "Nro Serie" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "empresa", label: "Empresa / Sucursal" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "tipo", label: "Tipo" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "kmCobrado", label: "KMs cob." }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "kmEsperado", label: "KMs esp." }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "cobrado", label: "Cobrado" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "esperado", label: "Esperado" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "diferencia", label: "Diferencia" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "fecha", label: "Fecha" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <th className={thCls}>Estado</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((inc) => (
              <IncidenteRow
                key={inc.id}
                liquidacionId={liquidacionId}
                prestadorId={prestadorId}
                prestadores={prestadores}
                incidente={inc}
                incidentesById={incidentesById}
                alertasInc={alertasByInc[inc.id] ?? []}
                expanded={expandedIds.has(inc.id)}
                isRutaCompartida={rutasCompartidas.has(inc.id)}
                onToggle={() => toggleExpanded(inc.id)}
                onAlertaChanged={onAlertaChanged}
              />
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex flex-wrap items-center justify-end gap-6 border-t border-border bg-muted/40 px-4 py-3 font-body text-sm">
        <span className="text-muted-foreground">
          KMs: <span className="text-foreground">{Math.round(totalKms).toLocaleString("es-AR")}</span>
        </span>
        <span className="text-muted-foreground">
          Costo servicio: <span className="text-foreground">{formatARS(totalServicio)}</span>
        </span>
        <span className="text-muted-foreground">
          Total general:{" "}
          <span className="font-semibold text-foreground">{formatARS(totalGeneral)}</span>
        </span>
      </div>
    </div>
  );
}
