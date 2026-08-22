"use client";

import type { ReactNode } from "react";
import type { ConsumableHistoryPoint } from "../../types";
import { EMPTY_VALUE } from "../../utils/format";

/** Etiquetas, helpers puros y primitivos de layout del modal de detalle de
 * consumible (`ConsumableDetailModal`). */

export const TYPE_LABELS: Record<string, string> = {
  TONER: "Tóner",
  INK: "Tinta",
  DRUM: "Tambor",
  WASTE: "Residuos",
  FUSER: "Fusor",
  TRANSFER_UNIT: "Unidad de transferencia",
  MAINTENANCE_KIT: "Kit de mantenimiento",
};

export const COLOUR_LABELS: Record<string, string> = {
  CYAN: "Cian",
  MAGENTA: "Magenta",
  YELLOW: "Amarillo",
  BLACK: "Negro",
  TRICOLOUR: "Tricolor",
  MULTICOLOUR: "Multicolor",
  NONE: "N/A",
  UNKNOWN: "Desconocido",
};

/** HP no publica un enum cerrado para `reason` (es texto libre): solo se
 * traduce lo visto en la práctica, el resto se muestra tal cual llega. */
export const REASON_LABELS: Record<string, string> = { "LOW TONER": "Nivel bajo" };

export function labelled(map: Record<string, string>, value: string | null | undefined): string {
  if (!value) return EMPTY_VALUE;
  return map[value] ?? value;
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h3 className="mb-2 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
      {children}
    </h3>
  );
}

export interface InfoRow {
  term: string;
  detail: ReactNode;
}

export function InfoList({ rows }: { rows: InfoRow[] }) {
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 font-body text-[12.5px] leading-snug">
      {rows.map((row, index) => (
        <div key={`${row.term}-${index}`} className="contents">
          <dt className="whitespace-nowrap text-muted-foreground">{row.term}</dt>
          <dd className="break-words text-right text-foreground">{row.detail}</dd>
        </div>
      ))}
    </dl>
  );
}

export function Note({ children }: { children: ReactNode }) {
  return <p className="font-body text-xs text-muted-foreground">{children}</p>;
}

export function StatBlock({
  label,
  value,
  size = "normal",
}: {
  label: string;
  value: ReactNode;
  size?: "normal" | "large";
}) {
  return (
    <div>
      <p className="font-body text-[11px] text-muted-foreground">{label}</p>
      <p
        className={
          size === "large"
            ? "mt-0.5 font-heading text-2xl font-extrabold text-brand-orange"
            : "mt-0.5 font-body text-[12.5px] font-bold text-foreground"
        }
      >
        {value}
      </p>
    </div>
  );
}

const LEGEND_ITEMS = [
  { swatch: <span className="h-2 w-2 rounded-full bg-[#ef4444]" />, label: "Solicitud actual" },
  {
    swatch: <span className="h-2 w-2 rounded-full bg-[#F7941D]" />,
    label: "Otras solicitudes",
  },
] as const;

export function ChartLegend({ showNoContact }: { showNoContact: boolean }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 font-body text-[11px] text-muted-foreground">
      {LEGEND_ITEMS.map((item) => (
        <span key={item.label} className="inline-flex items-center gap-1.5">
          {item.swatch}
          {item.label}
        </span>
      ))}
      {showNoContact && (
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-[2px] bg-[#a16207] dark:bg-[#eab308]" />
          Sin contacto
        </span>
      )}
    </div>
  );
}

/** Índice del punto del gráfico más cercano (hacia atrás) a una fecha dada. */
export function indexForDate(
  points: ConsumableHistoryPoint[],
  iso: string | null | undefined,
): number {
  if (!iso || points.length === 0) return -1;
  const target = new Date(iso).getTime();
  if (Number.isNaN(target)) return -1;
  let index = 0;
  for (let i = 0; i < points.length; i += 1) {
    const pointTime = new Date(points[i].date).getTime();
    if (Number.isNaN(pointTime) || pointTime > target) break;
    index = i;
  }
  return index;
}
