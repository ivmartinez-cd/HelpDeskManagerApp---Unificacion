import type { EquiposSinRealResumen } from "../types/equipos-sin-real";

function KpiCard({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className="flex min-w-[120px] flex-col gap-0.5 rounded-[12px] border border-border bg-card px-4 py-3">
      <span className={`font-heading text-2xl font-extrabold tabular-nums ${tone}`}>
        {new Intl.NumberFormat("es-AR").format(value)}
      </span>
      <span className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
    </div>
  );
}

/** Bloque de KPIs de severidad del análisis de "equipos sin contador real" —
 * extraído de `EquiposSinRealView` para no pasar el límite de 300 líneas del
 * archivo (ARCHITECTURE_GUIDE §4). */
export function EquiposSinRealResumenKpis({ resumen }: { resumen: EquiposSinRealResumen }) {
  return (
    <div className="flex flex-col gap-3">
      <h2 className="font-heading text-base font-bold text-foreground">Resumen</h2>
      <div className="flex flex-wrap gap-3">
        <KpiCard label="Sin real (1+ mes)" value={resumen.total} tone="text-foreground" />
        <KpiCard label="Críticos · 12+" value={resumen.criticos} tone="text-destructive" />
        <KpiCard label="Altos · 6-11" value={resumen.altos} tone="text-brand-orange" />
        <KpiCard label="Medios · 3-5" value={resumen.medios} tone="text-warning" />
        <KpiCard label="Nunca real" value={resumen.nunca_real} tone="text-destructive" />
        <KpiCard label="No localizado" value={resumen.no_localizados} tone="text-destructive" />
      </div>
    </div>
  );
}
