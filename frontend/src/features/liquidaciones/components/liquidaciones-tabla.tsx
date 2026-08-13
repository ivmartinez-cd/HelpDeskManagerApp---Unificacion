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
const tdCls = "py-3 px-4 font-body text-sm";

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
    <div
      className="overflow-hidden rounded-[12px]"
      style={{ background: "#1e1e1e", border: "1px solid rgba(255,255,255,.07)" }}
    >
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr style={{ background: "rgba(0,0,0,.2)" }}>
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
                  className="border-t transition-colors hover:bg-white/[0.03]"
                  style={{ borderColor: "rgba(255,255,255,.07)" }}
                >
                  <td className={tdCls}>
                    <Link
                      href={`/liquidaciones/${liq.id}`}
                      className="font-body text-sm text-brand-orange hover:underline"
                    >
                      {liq.nombreArchivo ?? `Liquidación ${liq.periodo}`}
                    </Link>
                  </td>
                  <td className={tdCls} style={{ color: "#e0e0e0" }}>
                    {pst ? `${pst.region ?? pst.nombreCorto} — ${pst.nombre}` : "—"}
                  </td>
                  <td className={tdCls} style={{ color: "#e0e0e0" }}>
                    {liq.periodo || "—"}
                  </td>
                  <td className={tdCls}>
                    <span
                      className="inline-flex items-center rounded-full px-2 py-0.5 font-body text-xs"
                      style={{
                        background: "rgba(255,255,255,.08)",
                        color: "rgba(255,255,255,.5)",
                      }}
                    >
                      {liq.tipoLiquidacion}
                    </span>
                  </td>
                  <td className={tdCls}>
                    <EstadoBadge estado={liq.estado} />
                  </td>
                  <td className={`${tdCls} text-right`} style={{ color: "#e0e0e0" }}>
                    {liq.totalIncidentes.toLocaleString("es-AR")}
                  </td>
                  <td className={`${tdCls} text-right`} style={{ color: "#e0e0e0" }}>
                    {formatARS(liq.totalImporte)}
                  </td>
                  <td className={tdCls} style={{ color: "rgba(255,255,255,.4)" }}>
                    {formatFecha(liq.fechaImportacion)}
                  </td>
                  <td className={tdCls}>
                    <button
                      onClick={() => onDelete(liq.id)}
                      className="font-body text-sm transition-opacity hover:opacity-70"
                      style={{ color: "#ef4444" }}
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
