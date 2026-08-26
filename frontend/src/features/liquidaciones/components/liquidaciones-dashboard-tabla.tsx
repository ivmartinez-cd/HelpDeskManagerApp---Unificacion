import Link from "next/link";
import { ExternalLink } from "lucide-react";
import type { Liquidacion, PrestadorLiquidacion } from "../types/liquidaciones";
import { formatARS, formatFecha } from "../lib/format";
import { EstadoBadge } from "./estado-badge";

const thCls =
  "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const tdCls = "py-3 px-4 font-body text-sm text-foreground";

export function LiquidacionesDashboardTabla({
  ultimas,
  prestadorMap,
}: {
  ultimas: Liquidacion[];
  prestadorMap: Record<string, PrestadorLiquidacion>;
}) {
  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="flex items-center justify-between px-4 pt-5 pb-3">
        <h2 className="font-heading text-base font-bold text-foreground">Últimas liquidaciones</h2>
        <Link href="/liquidaciones/lista" className="font-body text-sm text-brand-orange hover:underline">
          Ver todas
        </Link>
      </div>

      {ultimas.length === 0 ? (
        <p className="px-4 pb-6 font-body text-sm text-muted-foreground">
          Todavía no hay liquidaciones importadas.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-muted/40">
                <th className={thCls}>Prestador</th>
                <th className={thCls}>Período</th>
                <th className={thCls}>Estado</th>
                <th className={`${thCls} text-right`}>Incidentes</th>
                <th className={`${thCls} text-right`}>Importe</th>
                <th className={thCls}>Fecha de carga</th>
                <th className={thCls}>Web Agentes</th>
              </tr>
            </thead>
            <tbody>
              {ultimas.map((liq) => {
                const pst = prestadorMap[liq.prestadorId];
                return (
                  <tr key={liq.id} className="border-t border-border transition-colors hover:bg-muted/30">
                    <td className={tdCls}>
                      {pst ? `${pst.region ?? pst.nombreCorto} — ${pst.nombre}` : liq.prestadorId.slice(0, 8)}
                    </td>
                    <td className={tdCls}>{liq.periodo || "—"}</td>
                    <td className={tdCls}>
                      <EstadoBadge estado={liq.estado} />
                    </td>
                    <td className={`${tdCls} text-right`}>{liq.totalIncidentes.toLocaleString("es-AR")}</td>
                    <td className={`${tdCls} text-right`}>{formatARS(liq.totalImporte)}</td>
                    <td className={`${tdCls} text-muted-foreground`}>{formatFecha(liq.fechaImportacion)}</td>
                    <td className={tdCls}>
                      {liq.numeroLiquidacion ? (
                        <a
                          href={`https://webagentes.canaldirecto.com.ar/liquidations/view/${liq.numeroLiquidacion}`}
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
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
