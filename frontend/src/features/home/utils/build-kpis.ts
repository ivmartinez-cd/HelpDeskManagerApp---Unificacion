import type { ResumenClientesOperador } from "@/features/contadores/types/calendario";
import type { PrestadoresResumen } from "@/features/prestadores/types/prestadores";
import type { SlaResumen } from "@/features/sla/types/sla";
import type { KpiDef } from "../components/kpi-strip";
import { TREND_DOWN, TREND_UP } from "../components/kpi-strip";
import type { CalendarioHome, Remote, SlaHistoria } from "../hooks/use-inicio-data";
import { fmtInt, fmtPct } from "./inicio-format";

const VALUE_RED = "#c98484";
const VALUE_AMBER = "#c4a35a";
const SPARK_SLA = "#6f9c7f";

function valor<T>(remote: Remote<T>, render: (data: T) => string): string | null {
  if (remote.loading) return null;
  if (remote.error || remote.data === null) return "—";
  return render(remote.data);
}

/** Franja KPI de Inicio, solo con datos reales: la única serie histórica
 * disponible es la de SLA (resúmenes mensuales), así que es la única con
 * sparkline/tendencia — el resto muestra el valor actual sin historia
 * inventada (decisión explícita del proyecto: nada de datos falsos). */
export function buildKpis(gates: {
  prestadores: boolean;
  contadores: boolean;
  sla: boolean;
  liquidaciones: boolean;
  parque: Remote<PrestadoresResumen>;
  contadoresResumen: Remote<ResumenClientesOperador>;
  slaHistoria: Remote<SlaHistoria>;
  calendario: Remote<CalendarioHome>;
  liquidacionesPendientes: Remote<{ pendientes: number }>;
}): KpiDef[] {
  const kpis: KpiDef[] = [];
  const { parque, contadoresResumen, slaHistoria, calendario, liquidacionesPendientes } = gates;

  if (gates.prestadores) {
    kpis.push({
      label: "Parque total",
      value: valor(parque, (r) =>
        fmtInt(
          r.grupos.reduce(
            (sum, g) =>
              sum +
              g.prestadores.filter((p) => p.isActive).reduce((s, p) => s + (p.equipos ?? 0), 0),
            0,
          ),
        ),
      ),
      sub: "impresoras",
    });
  }

  if (gates.contadores) {
    kpis.push({
      label: "Clientes del mes",
      value: valor(contadoresResumen, (r) => fmtInt(r.total_clientes)),
      sub: "activos",
    });
  }

  if (gates.sla) {
    const actual = slaHistoria.data?.resumenes.at(-1) ?? null;
    const anterior = slaHistoria.data?.resumenes.at(-2) ?? null;
    const variacion =
      actual && anterior && anterior.total > 0 ? actual.pct_correctos - anterior.pct_correctos : null;
    const serie =
      slaHistoria.data?.resumenes
        .filter((r): r is SlaResumen => r !== null && r.total > 0)
        .map((r) => r.pct_correctos) ?? [];
    kpis.push({
      label: "SLA del mes",
      value: valor(slaHistoria, () => (actual ? `${fmtPct(actual.pct_correctos)}%` : "—")),
      sub: actual ? `de ${fmtInt(actual.total)}` : "",
      trend:
        variacion === null
          ? null
          : {
              text: `${variacion >= 0 ? "▲" : "▼"} ${fmtPct(Math.abs(variacion))}%`,
              color: variacion >= 0 ? TREND_UP : TREND_DOWN,
            },
      spark: serie.length >= 2 ? { data: serie, color: SPARK_SLA } : null,
    });
    const difVencidos =
      actual && anterior && anterior.total > 0 ? actual.vencidos - anterior.vencidos : null;
    kpis.push({
      label: "Vencidos",
      value: valor(slaHistoria, () => (actual ? fmtInt(actual.vencidos) : "—")),
      sub: "incidentes",
      valueColor: VALUE_RED,
      trend:
        difVencidos === null || difVencidos === 0
          ? null
          : {
              text: `${difVencidos > 0 ? "+" : "−"}${fmtInt(Math.abs(difVencidos))}`,
              color: difVencidos > 0 ? TREND_DOWN : TREND_UP,
            },
    });
  }

  if (gates.contadores) {
    kpis.push({
      label: "Pendientes",
      value: valor(calendario, (c) => fmtInt(c.pendientes.length)),
      sub: "facturación sin cerrar",
      valueColor: VALUE_AMBER,
    });
  }

  if (gates.liquidaciones) {
    kpis.push({
      label: "Sin aprobar",
      value: valor(liquidacionesPendientes, (r) => fmtInt(r.pendientes)),
      sub: "liquidaciones",
      valueColor: VALUE_AMBER,
    });
  }

  return kpis;
}
