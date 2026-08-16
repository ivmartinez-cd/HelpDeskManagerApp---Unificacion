"use client";

import { ArcElement, Chart as ChartJS, Tooltip } from "chart.js";
import { Doughnut } from "react-chartjs-2";
import { fmtInt, fmtPct } from "../utils/inicio-format";

ChartJS.register(ArcElement, Tooltip);

export interface DonutRow {
  id: string;
  nombre: string;
  /** Detalle junto al nombre: "13 PST", "37 clientes"... Opcional. */
  detalle?: string;
  color: string;
  valor: number;
}

/** Dona por operador + leyenda "nombre · detalle · % · valor" — vista
 * compartida entre "Distribución del parque" y "Contadores por operador"
 * (el handoff las define idénticas). */
export function OperadorDonut({
  rows,
  total,
  centerSub,
  tooltipUnidad,
}: {
  rows: DonutRow[];
  total: number;
  centerSub: string;
  tooltipUnidad: string;
}) {
  return (
    <>
      <div className="relative mx-auto my-1.5 flex h-[130px] w-[130px] items-center justify-center">
        <Doughnut
          data={{
            labels: rows.map((r) => r.nombre),
            datasets: [
              {
                data: rows.map((r) => r.valor),
                backgroundColor: rows.map((r) => r.color),
                borderWidth: 2,
                borderColor: "hsl(240 10% 7%)",
                hoverOffset: 5,
              },
            ],
          }}
          options={{
            cutout: "70%",
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: (c) => ` ${c.label}: ${fmtInt(c.raw as number)} ${tooltipUnidad}`,
                },
              },
            },
          }}
        />
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-heading text-[18px] font-extrabold leading-none text-foreground">
            {fmtInt(total)}
          </span>
          <span className="font-body text-[10.5px] text-muted-foreground">{centerSub}</span>
        </div>
      </div>
      <div className="flex flex-col gap-[7px]">
        {rows.map((r) => (
          <div key={r.id} className="flex items-center gap-2">
            <span
              className="h-[9px] w-[9px] shrink-0 rounded-[3px]"
              style={{ background: r.color }}
            />
            <span className="min-w-0 flex-1 truncate font-body text-[12.5px] font-semibold text-foreground/70">
              {r.nombre}{r.detalle ? ` · ${r.detalle}` : ""}
            </span>
            <span className="shrink-0 font-body text-[12px] font-semibold text-muted-foreground">
              {total > 0 ? `${fmtPct((r.valor / total) * 100)}%` : "—"}
            </span>
            <span className="min-w-[44px] shrink-0 text-right font-heading text-[12.5px] font-bold text-foreground">
              {fmtInt(r.valor)}
            </span>
          </div>
        ))}
      </div>
    </>
  );
}
