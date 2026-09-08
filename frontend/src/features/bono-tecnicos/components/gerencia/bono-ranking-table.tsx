"use client";

import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import { BonoSparkline } from "./bono-sparkline";
import type { EvolucionTecnico } from "../../types/bono-tecnicos";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { compareSortValues } from "@/shared/hooks/use-table-sort";
import type { SortState } from "@/shared/hooks/use-table-sort";

export type BonoRankingSortKey = "tecnico" | "puntaje_promedio" | "delta" | "incidentes" | "tv";

const numberFormat = new Intl.NumberFormat("es-AR");
const decimalFormat = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 });

function DeltaCell({
  tecnico,
  promedioEquipo,
}: {
  tecnico: EvolucionTecnico;
  promedioEquipo: number | null;
}) {
  if (tecnico.puntaje_promedio === null || promedioEquipo === null) {
    return <span className="text-muted-foreground">—</span>;
  }
  const diff = tecnico.puntaje_promedio - promedioEquipo;
  const Icon = diff > 0.05 ? ArrowUpRight : diff < -0.05 ? ArrowDownRight : Minus;
  return (
    <span className="inline-flex items-center gap-1 tabular-nums text-muted-foreground">
      <Icon className="h-3.5 w-3.5 flex-none" aria-hidden="true" />
      {diff >= 0 ? "+" : ""}
      {decimalFormat.format(diff)}
    </span>
  );
}

interface BonoRankingTableProps {
  tecnicos: EvolucionTecnico[];
  promedioEquipo: number | null;
  sort: SortState<BonoRankingSortKey>;
  onToggleSort: (key: BonoRankingSortKey) => void;
  onVerTecnico: (tecnico: EvolucionTecnico) => void;
}

function sortValue(tecnico: EvolucionTecnico, key: BonoRankingSortKey): string | number | null {
  switch (key) {
    case "tecnico":
      return tecnico.tecnico;
    case "puntaje_promedio":
      return tecnico.puntaje_promedio;
    case "delta":
      return tecnico.puntaje_promedio;
    case "incidentes":
      return tecnico.incidentes_total;
    case "tv":
      return tecnico.tv_aprobadas_total;
  }
}

export function BonoRankingTable({
  tecnicos,
  promedioEquipo,
  sort,
  onToggleSort,
  onVerTecnico,
}: BonoRankingTableProps) {
  const ordenados = [...tecnicos].sort((a, b) =>
    compareSortValues(sortValue(a, sort.key), sortValue(b, sort.key), sort.direction),
  );

  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full min-w-[900px] text-left text-sm">
        <thead>
          <tr className="border-b border-border font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            <SortableHeader
              column={{ key: "tecnico", label: "Técnico" }}
              sort={sort}
              onToggleSort={onToggleSort}
              thClassName="px-4 py-2.5"
            />
            <SortableHeader
              column={{ key: "puntaje_promedio", label: "Puntaje promedio" }}
              sort={sort}
              onToggleSort={onToggleSort}
              thClassName="px-4 py-2.5 text-right"
            />
            <SortableHeader
              column={{ key: "delta", label: "vs. equipo" }}
              sort={sort}
              onToggleSort={onToggleSort}
              thClassName="px-4 py-2.5 text-right"
            />
            <SortableHeader
              column={{ key: "incidentes", label: "Incidentes" }}
              sort={sort}
              onToggleSort={onToggleSort}
              thClassName="px-4 py-2.5 text-right"
            />
            <SortableHeader
              column={{ key: "tv", label: "TV aprobadas" }}
              sort={sort}
              onToggleSort={onToggleSort}
              thClassName="px-4 py-2.5 text-right"
            />
            <th className="px-4 py-2.5">Últimos 12 meses</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {ordenados.map((tecnico) => (
            <tr key={tecnico.id_tecnico} className="hover:bg-muted/30">
              <td className="px-4 py-3">
                <button
                  type="button"
                  onClick={() => onVerTecnico(tecnico)}
                  className="font-semibold text-brand-orange no-underline hover:underline"
                >
                  {tecnico.tecnico}
                </button>
              </td>
              <td className="px-4 py-3 text-right font-bold tabular-nums text-brand-orange">
                {tecnico.puntaje_promedio !== null
                  ? decimalFormat.format(tecnico.puntaje_promedio)
                  : "—"}
              </td>
              <td className="px-4 py-3 text-right">
                <DeltaCell tecnico={tecnico} promedioEquipo={promedioEquipo} />
              </td>
              <td className="px-4 py-3 text-right tabular-nums">
                {numberFormat.format(tecnico.incidentes_total)}
              </td>
              <td className="px-4 py-3 text-right tabular-nums">
                {numberFormat.format(tecnico.tv_aprobadas_total)}
                <span className="text-muted-foreground">
                  {" "}
                  / {numberFormat.format(tecnico.tv_solicitadas_total)}
                </span>
              </td>
              <td className="px-4 py-3">
                <BonoSparkline puntajes={tecnico.puntos.map((p) => p.puntaje)} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
