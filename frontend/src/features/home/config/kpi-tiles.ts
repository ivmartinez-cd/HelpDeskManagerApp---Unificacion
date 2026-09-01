import { nivelEspera, textoEspera } from "@/features/wati/utils/espera";
import type { DashboardData } from "../hooks/use-dashboard-data";
import { fmtInt, fmtPct } from "../utils/inicio-format";
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
    { id: "pendientes-cerrar", label: "Incidentes", href: "/sla/pendientes-a-cerrar" },
    d.pendientesResumen,
    {
      value: fmtInt(total),
      context: total === 0 ? "sin incidentes" : "finalizados sin cerrar",
      tone: total === 0 ? "ok" : "warn",
    },
  );
}

/** Anexos sin proceso generado: el operador se olvidó de iniciar la
 * facturación de un anexo (sin Nro_Proceso del último período ya cerrado
 * con seguridad, ver ListarAnexosSinProcesar en el backend). El número
 * grande son CLIENTES (así lo mira el operador: "a quién le falta"); el
 * contexto, los anexos concretos que hay que ir a generar. Sin dato de
 * Siges el tile queda en error ("—", "no se pudo cargar"), no en 0: un cero
 * inventado hace perder confianza en el KPI. */
function kpiAnexosSinProcesar(d: DashboardData): KpiTile {
  const r = d.anexosSinProcesar.data;
  const clientes = r?.clientes ?? 0;
  const anexos = r?.anexos ?? 0;
  return tile(
    {
      id: "anexos-sin-procesar",
      label: "Sin procesar",
      href: "/contadores/anexos-sin-procesar",
    },
    d.anexosSinProcesar,
    {
      value: fmtInt(clientes),
      context:
        clientes === 0
          ? "todos procesados"
          : `${fmtInt(anexos)} ${anexos === 1 ? "anexo" : "anexos"} sin procesar`,
      tone: clientes === 0 ? "ok" : "bad",
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

/** Franja de estado de Inicio: solo lo accionable (5 tiles como máximo,
 * feedback TL 2026-08-22), en orden de urgencia operativa. Sin historia inventada: cada tile muestra el dato
 * actual y su contexto; la única variación real es la de SLA (mes anterior). */
export function buildKpiTiles(d: DashboardData, access: ModuleAccess): KpiTile[] {
  const tiles: (KpiTile | null)[] = [
    access.wati ? kpiWhatsapp(d) : null,
    access.insumos ? kpiInsumos(d) : null,
    access.contadores ? kpiAnexosSinProcesar(d) : null,
    access.sla ? kpiPendientesCerrar(d) : null,
    access.sla ? kpiSla(d) : null,
    access.liquidaciones ? kpiLiquidaciones(d) : null,
  ];
  return tiles.filter((t): t is KpiTile => t !== null);
}
