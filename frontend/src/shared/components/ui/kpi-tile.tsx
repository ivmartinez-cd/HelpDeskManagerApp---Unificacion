import type { ReactNode } from "react";
import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";
import { cn } from "@/shared/utils/cn";

/** Lo que se muestra cuando el dato no vino (mismo criterio que el
 * EMPTY_VALUE de utils/format de insumos, duplicado acá para que la primitiva
 * compartida no dependa de una feature). */
const EMPTY_VALUE = "—";

/** Tile KPI de las pantallas de Estadísticas (Patrón 2 del handoff: número
 * Montserrat 800 22px en el color de la métrica, sobre superficie de card).
 *
 * El delta contra el período anterior se muestra en gris: el backend ya manda
 * los totales del período previo, pero "más pedidos" no es ni bueno ni malo —
 * pintarlo de verde/rojo inventaría una semántica que el legacy no tiene.
 */

export type KpiTone = "orange" | "neutral" | "danger";

const valueToneClass: Record<KpiTone, string> = {
  orange: "text-brand-orange",
  neutral: "text-foreground",
  danger: "text-[#dc2626] dark:text-[#f87171]",
};

export interface KpiDelta {
  current: number;
  previous: number;
  /** Texto del período anterior, p.ej. "13/06/2026 – 12/07/2026". */
  periodLabel?: string;
}

interface KpiTileProps {
  label: string;
  value: string;
  tone?: KpiTone;
  /** Línea chica debajo del número (contexto, no métrica). */
  hint?: ReactNode;
  delta?: KpiDelta;
  className?: string;
}

function DeltaLine({ current, previous, periodLabel }: KpiDelta) {
  const diff = current - previous;
  const pct = previous > 0 ? (diff / previous) * 100 : null;
  const Icon = diff > 0 ? ArrowUpRight : diff < 0 ? ArrowDownRight : ArrowRight;
  const label =
    pct === null
      ? previous === 0 && current === 0
        ? "sin actividad previa"
        : `${diff >= 0 ? "+" : ""}${diff.toLocaleString("es-AR")} vs. período anterior`
      : `${diff >= 0 ? "+" : ""}${pct.toLocaleString("es-AR", {
          maximumFractionDigits: 1,
        })}% vs. período anterior`;

  return (
    <span
      className="mt-1.5 inline-flex items-center gap-1 font-body text-xs text-muted-foreground"
      title={periodLabel ? `Período anterior: ${periodLabel}` : undefined}
    >
      <Icon className="h-3.5 w-3.5 flex-none" aria-hidden="true" />
      {label}
    </span>
  );
}

export function KpiTile({ label, value, tone = "neutral", hint, delta, className }: KpiTileProps) {
  return (
    <div
      data-print-card
      className={cn("rounded-[12px] border border-border bg-card p-5", className)}
    >
      <span className="font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
        {label}
      </span>
      <div
        className={cn(
          "mt-1.5 font-heading text-[22px] font-extrabold leading-tight",
          valueToneClass[tone],
        )}
      >
        {value || EMPTY_VALUE}
      </div>
      {hint && (
        <div className="mt-1 font-body text-xs text-muted-foreground">{hint}</div>
      )}
      {delta && <DeltaLine {...delta} />}
    </div>
  );
}

/** Grilla estándar de tiles: 3 columnas como pide el handoff, con escalones
 * intermedios para no romper en pantallas chicas ni en impresión. */
export function KpiGrid({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("grid gap-4 sm:grid-cols-2 lg:grid-cols-3", className)}>{children}</div>
  );
}
