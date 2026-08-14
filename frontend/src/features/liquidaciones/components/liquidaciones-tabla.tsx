"use client";

import { useMemo } from "react";
import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";
import type { Liquidacion, PrestadorLiquidacion } from "../types/liquidaciones";
import { EstadoBadge } from "./estado-badge";

type LiqSortKey = "prestador" | "periodo" | "tipo" | "estado" | "incidentes" | "importe" | "fecha";
const LIQ_SORT_KEYS: readonly LiqSortKey[] = [
  "prestador", "periodo", "tipo", "estado", "incidentes", "importe", "fecha",
];

const WEB_AGENTES_BASE = "https://webagentes.canaldirecto.com.ar/liquidations/view";

function formatARS(n: number) {
  return n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 2 });
}

function formatFecha(iso: string) {
  const d = new Date(iso);
  return `${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`;
}

const thCls =
  "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const tdCls = "py-3 px-4 font-body text-sm text-foreground";

export function LiquidacionesTabla({
  items,
  prestadorMap,
  onDelete,
}: {
  items: Liquidacion[];
  prestadorMap: Record<string, PrestadorLiquidacion>;
  onDelete: (id: string) => void;
}) {
  const { sort, toggleSort } = useTableSort<LiqSortKey>({
    initial: { key: "fecha", direction: "desc" },
    keys: LIQ_SORT_KEYS,
    descFirstKeys: ["fecha"],
  });

  const sorted = useMemo(() => {
    const getSv = (liq: Liquidacion) => {
      const pst = prestadorMap[liq.prestadorId];
      switch (sort.key) {
        case "prestador": return pst ? `${pst.region ?? pst.nombreCorto} — ${pst.nombre}` : "";
        case "periodo": return liq.periodo;
        case "tipo": return liq.tipoLiquidacion;
        case "estado": return liq.estado;
        case "incidentes": return liq.totalIncidentes;
        case "importe": return liq.totalImporte;
        case "fecha": return liq.fechaImportacion;
      }
    };
    return [...items].sort((a, b) => compareSortValues(getSv(a), getSv(b), sort.direction));
  }, [items, prestadorMap, sort]);

  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-muted/40">
              <th className={thCls}>Archivo</th>
              <SortableHeader column={{ key: "prestador", label: "Prestador" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "periodo", label: "Período" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "tipo", label: "Tipo" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "estado", label: "Estado" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "incidentes", label: "Incidentes" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "importe", label: "Importe" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "fecha", label: "Fecha" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <th className={thCls}>Web Agentes</th>
              <th className={thCls}></th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((liq) => {
              const pst = prestadorMap[liq.prestadorId];
              return (
                <tr
                  key={liq.id}
                  className="border-t border-border transition-colors hover:bg-muted/30"
                >
                  <td className={tdCls}>
                    <Link
                      href={`/liquidaciones/${liq.id}`}
                      className="font-body text-sm text-brand-orange hover:underline"
                    >
                      {liq.nombreArchivo ?? `Liquidación ${liq.periodo}`}
                    </Link>
                  </td>
                  <td className={tdCls}>
                    {pst ? `${pst.region ?? pst.nombreCorto} — ${pst.nombre}` : "—"}
                  </td>
                  <td className={tdCls}>{liq.periodo || "—"}</td>
                  <td className={tdCls}>
                    <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 font-body text-xs text-muted-foreground">
                      {liq.tipoLiquidacion}
                    </span>
                  </td>
                  <td className={tdCls}>
                    <EstadoBadge estado={liq.estado} />
                  </td>
                  <td className={`${tdCls} text-right`}>
                    {liq.totalIncidentes.toLocaleString("es-AR")}
                  </td>
                  <td className={`${tdCls} text-right`}>{formatARS(liq.totalImporte)}</td>
                  <td className={`${tdCls} text-muted-foreground`}>
                    {formatFecha(liq.fechaImportacion)}
                  </td>
                  <td className={tdCls}>
                    {liq.numeroLiquidacion ? (
                      <a
                        href={`${WEB_AGENTES_BASE}/${liq.numeroLiquidacion}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 font-body text-sm text-brand-orange hover:underline"
                      >
                        {liq.numeroLiquidacion}
                        <ExternalLink size={12} />
                      </a>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className={tdCls}>
                    <button
                      onClick={() => onDelete(liq.id)}
                      className="font-body text-sm text-destructive transition-opacity hover:opacity-70"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
