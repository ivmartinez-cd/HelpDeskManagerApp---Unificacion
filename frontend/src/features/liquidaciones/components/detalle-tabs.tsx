"use client";

import { cn } from "@/shared/utils/cn";

export type DetalleTab = "detalle" | "modificaciones" | "facturacion" | "bitacora";

const TABS: { key: DetalleTab; label: string }[] = [
  { key: "detalle", label: "Incidentes y alertas" },
  { key: "modificaciones", label: "Modificaciones" },
  { key: "facturacion", label: "Facturación" },
  { key: "bitacora", label: "Bitácora" },
];

interface DetalleTabsProps {
  value: DetalleTab;
  onChange: (tab: DetalleTab) => void;
  /** Contador al lado del label; `null`/ausente = sin contador (o cargando). */
  counts: Partial<Record<DetalleTab, number | null>>;
  /** Pestañas con algo sin ver: el contador se pinta naranja aunque no esté activa. */
  destacadas?: Partial<Record<DetalleTab, boolean>>;
}

/** Pestañas del detalle de una liquidación, para que los incidentes no
 * queden abajo de todo lo demás. */
export function DetalleTabs({ value, onChange, counts, destacadas = {} }: DetalleTabsProps) {
  return (
    <div role="tablist" className="flex gap-1 border-b border-border">
      {TABS.map((tab) => {
        const active = tab.key === value;
        const count = counts[tab.key];
        return (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(tab.key)}
            className={cn(
              "-mb-px flex cursor-pointer items-center gap-2 border-b-2 px-3.5 py-2.5 font-body text-[13px] transition-colors",
              active
                ? "border-brand-orange font-bold text-brand-orange"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {tab.label}
            {count !== null && count !== undefined && (
              <span
                className={cn(
                  "rounded-[20px] px-1.5 py-0.5 font-body text-[10px] font-bold tabular-nums",
                  active || destacadas[tab.key]
                    ? "bg-brand-orange text-white"
                    : "bg-muted text-muted-foreground",
                )}
              >
                {count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
