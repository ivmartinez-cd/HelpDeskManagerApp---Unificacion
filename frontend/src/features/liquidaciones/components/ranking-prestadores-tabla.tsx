"use client";

import { useMemo } from "react";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";
import type { RankingPrestador } from "../types/liquidaciones";
import { formatARS } from "../lib/format";

type RankingSortKey = "prestador" | "importe" | "liquidaciones";
const RANKING_SORT_KEYS: readonly RankingSortKey[] = ["prestador", "importe", "liquidaciones"];
const TOP_N = 15;

const thCls =
  "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const tdCls = "py-3 px-4 font-body text-sm text-foreground";

export function RankingPrestadoresTabla({ items }: { items: RankingPrestador[] }) {
  const { sort, toggleSort } = useTableSort<RankingSortKey>({
    initial: { key: "importe", direction: "desc" },
    keys: RANKING_SORT_KEYS,
    descFirstKeys: ["importe", "liquidaciones"],
  });

  // Top 15 por facturado (el criterio del ranking) — el sort de columna solo
  // reordena ese mismo grupo, no trae prestadores nuevos al cambiar de columna.
  const top15 = useMemo(
    () => [...items].sort((a, b) => b.totalImporte - a.totalImporte).slice(0, TOP_N),
    [items],
  );

  const sorted = useMemo(() => {
    const getSv = (r: RankingPrestador) => {
      switch (sort.key) {
        case "prestador":
          return r.nombreCorto;
        case "importe":
          return r.totalImporte;
        case "liquidaciones":
          return r.cantidadLiquidaciones;
      }
    };
    return [...top15].sort((a, b) => compareSortValues(getSv(a), getSv(b), sort.direction));
  }, [top15, sort]);

  if (items.length === 0) {
    return (
      <p className="font-body text-sm text-muted-foreground">
        Todavía no hay liquidaciones importadas.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="bg-muted/40">
            <SortableHeader
              column={{ key: "prestador", label: "Prestador" }}
              sort={sort}
              onToggleSort={toggleSort}
              thClassName={thCls}
            />
            <SortableHeader
              column={{ key: "importe", label: "Total facturado" }}
              sort={sort}
              onToggleSort={toggleSort}
              thClassName={`${thCls} text-right`}
            />
            <SortableHeader
              column={{ key: "liquidaciones", label: "Liquidaciones" }}
              sort={sort}
              onToggleSort={toggleSort}
              thClassName={`${thCls} text-right`}
            />
          </tr>
        </thead>
        <tbody>
          {sorted.map((r) => (
            <tr key={r.nombreCorto} className="border-t border-border transition-colors hover:bg-muted/30">
              <td className={tdCls}>{r.nombreCorto}</td>
              <td className={`${tdCls} text-right`}>{formatARS(r.totalImporte)}</td>
              <td className={`${tdCls} text-right`}>
                {r.cantidadLiquidaciones.toLocaleString("es-AR")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
