"use client";

import Link from "next/link";
import type { Liquidacion, PrestadorLiquidacion } from "../types/liquidaciones";
import { EstadoBadge } from "./estado-badge";

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
  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-muted/40">
              <th className={thCls}>Archivo</th>
              <th className={thCls}>Prestador</th>
              <th className={thCls}>Período</th>
              <th className={thCls}>Tipo</th>
              <th className={thCls}>Estado</th>
              <th className={`${thCls} text-right`}>Incidentes</th>
              <th className={`${thCls} text-right`}>Importe</th>
              <th className={thCls}>Fecha</th>
              <th className={thCls}></th>
            </tr>
          </thead>
          <tbody>
            {items.map((liq) => {
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
