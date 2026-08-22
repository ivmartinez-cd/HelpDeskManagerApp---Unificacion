import { nivelEspera, textoEspera } from "@/features/wati/utils/espera";
import type { DashboardData } from "../hooks/use-dashboard-data";
import { AGING_BUCKETS, fmtInt, fmtPct } from "../utils/inicio-format";
import { totalParque } from "../utils/parque";
import type { ModuleAccess } from "./dashboard-registry";

export type KpiTone = "neutral" | "ok" | "warn" | "bad";

export interface KpiTile {
  id: string;
  label: string;
  value: string;
  /** Contexto corto debajo del valor ("3 críticos", "de 614"). */
  context: string;
  tone: KpiTone;
  href: string;
  loading: boolean;
  error: boolean;
}

function tile(
  base: Pick<KpiTile, "id" | "label" | "href">,
  remote: { loading: boolean; error: string | null },
  resolved: Pick<KpiTile, "value" | "context" | "tone">,
): KpiTile {
  return { ...base, ...resolved, loading: remote.loading, error: remote.error !== null };
}

function kpiWhatsapp(d: DashboardData): KpiTile {
  const r = d.watiPendientes.resumen;
  const total = r?.total ?? 0;
  const nivel = nivelEspera(r?.max_minutos_esperando ?? 0);
  return tile(
    { id: "wati", label: "WhatsApp", href: "/wati" },
    { loading: d.watiPendientes.loading, error: d.watiPendientes.error },
    {
      value: fmtInt(total),
      context:
        total === 0
          ? "todo respondido"
          : `el más viejo ${textoEspera(r?.max_minutos_esperando ?? 0)}`,
      tone: total === 0 ? "ok" : nivel === "critico" ? "bad" : "warn",
    },
  );
}

function kpiInsumos(d: DashboardData): KpiTile {
  const t = d.insumosDashboard.data?.totals ?? {};
  const pending = t.pending ?? 0;
  const critical = t.critical ?? 0;
  return tile(
    { id: "insumos", label: "Insumos", href: "/insumos" },
    d.insumosDashboard,
    {
      value: fmtInt(pending),
      context: pending === 0 ? "sin solicitudes" : `${fmtInt(critical)} críticos sin cargar`,
      tone: critical > 0 ? "bad" : pending > 0 ? "warn" : "ok",
    },
  );
}

function kpiPendientesCerrar(d: DashboardData): KpiTile {
  const total = d.pendientesResumen.data?.total ?? 0;
  return tile(
    { id: "pendientes-cerrar", label: "Pend. a cerrar", href: "/sla/pendientes-a-cerrar" },
    d.pendientesResumen,
    {
      value: fmtInt(total),
      context: total === 0 ? "sin incidentes" : "finalizados sin cerrar",
      tone: total === 0 ? "ok" : "warn",
    },
  );
}

function kpiFacturacion(d: DashboardData): KpiTile {
  const pendientes = d.calendario.data?.pendientes ?? [];
  const hoy = new Date();
  const viejos = pendientes.filter((p) => {
    const dias = Math.round((hoy.getTime() - Date.parse(p.start)) / 86_400_000);
    return dias > AGING_BUCKETS[3].max;
  }).length;
  return tile(
    { id: "facturacion", label: "Facturación", href: "/contadores/calendario" },
    d.calendario,
    {
      value: fmtInt(pendientes.length),
      context:
        pendientes.length === 0 ? "todo cerrado" : `${fmtInt(viejos)} con más de 10 días`,
      tone: viejos > 0 ? "bad" : pendientes.length > 0 ? "warn" : "ok",
    },
  );
}

function kpiSla(d: DashboardData): KpiTile {
  const h = d.slaHistoria.data;
  const actual = h?.resumenes[h.resumenes.length - 1] ?? null;
  const anterior = h?.resumenes[h.resumenes.length - 2] ?? null;
  const variacion =
    actual && anterior && anterior.total > 0 ? actual.pct_correctos - anterior.pct_correctos : null;
  const sinDatos = !actual || actual.total === 0;
  return tile(
    { id: "sla", label: "SLA del mes", href: "/sla" },
    d.slaHistoria,
    {
      value: sinDatos ? "—" : `${fmtPct(actual.pct_correctos)}%`,
      context: sinDatos
        ? "sin incidentes"
        : variacion === null
          ? `${fmtInt(actual.vencidos)} vencidos de ${fmtInt(actual.total)}`
          : `${variacion >= 0 ? "▲" : "▼"} ${fmtPct(Math.abs(variacion))} pp vs. mes ant.`,
      tone: sinDatos ? "neutral" : variacion !== null && variacion < 0 ? "warn" : "ok",
    },
  );
}

function kpiLiquidaciones(d: DashboardData): KpiTile {
  const total = d.liquidacionesPendientes.data?.pendientes ?? 0;
  return tile(
    { id: "liquidaciones", label: "Liquidaciones", href: "/liquidaciones" },
    d.liquidacionesPendientes,
    {
      value: fmtInt(total),
      context: total === 0 ? "al día" : "sin aprobar",
      tone: total === 0 ? "ok" : "warn",
    },
  );
}

function kpiClientesHoy(d: DashboardData): KpiTile {
  const n = d.calendario.data?.hoy.length ?? 0;
  return tile(
    { id: "clientes-hoy", label: "Clientes hoy", href: "/contadores/calendario" },
    d.calendario,
    { value: fmtInt(n), context: n === 1 ? "visita planificada" : "visitas planificadas", tone: "neutral" },
  );
}

function kpiParque(d: DashboardData): KpiTile {
  const total = d.parque.data ? totalParque(d.parque.data) : 0;
  return tile(
    { id: "parque", label: "Parque", href: "/prestadores" },
    d.parque,
    { value: fmtInt(total), context: "impresoras en PST activos", tone: "neutral" },
  );
}

/** Franja de estado de Inicio: un tile por módulo visible, en orden de
 * urgencia operativa. Sin historia inventada: cada tile muestra el dato
 * actual y su contexto; la única variación real es la de SLA (mes anterior). */
export function buildKpiTiles(d: DashboardData, access: ModuleAccess): KpiTile[] {
  const tiles: (KpiTile | null)[] = [
    access.wati ? kpiWhatsapp(d) : null,
    access.insumos ? kpiInsumos(d) : null,
    access.sla ? kpiPendientesCerrar(d) : null,
    access.contadores ? kpiFacturacion(d) : null,
    access.sla ? kpiSla(d) : null,
    access.liquidaciones ? kpiLiquidaciones(d) : null,
    access.contadores ? kpiClientesHoy(d) : null,
    access.cardParque ? kpiParque(d) : null,
  ];
  return tiles.filter((t): t is KpiTile => t !== null);
}
