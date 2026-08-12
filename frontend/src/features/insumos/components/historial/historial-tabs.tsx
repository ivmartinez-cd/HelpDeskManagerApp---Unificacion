"use client";

import { cn } from "@/shared/utils/cn";

/** Las 5 pestañas del Historial, sincronizadas con `?tab=` (los mismos valores
 * que el legacy, para que los bookmarks y el redirect `/pedidos →
 * /historial?tab=pendientes` sigan funcionando). */
export type HistorialTab = "pendientes" | "orders" | "system" | "all" | "mails";

export const HISTORIAL_TABS: { key: HistorialTab; label: string }[] = [
  { key: "pendientes", label: "Pedidos Pendientes" },
  { key: "orders", label: "Solo Pedidos" },
  { key: "system", label: "Acciones del Sistema" },
  { key: "all", label: "Todos los Registros" },
  { key: "mails", label: "Mails enviados" },
];

export const DEFAULT_TAB: HistorialTab = "pendientes";

export function isHistorialTab(value: string | null | undefined): value is HistorialTab {
  return HISTORIAL_TABS.some((tab) => tab.key === value);
}

/** Las tres pestañas que comparten la tabla plana de auditoría. */
export function isAuditTab(tab: HistorialTab): boolean {
  return tab === "orders" || tab === "system" || tab === "all";
}

interface HistorialTabsProps {
  value: HistorialTab;
  onChange: (tab: HistorialTab) => void;
  /** Contador al lado del label. `null`/ausente = todavía no se sabe. */
  counts: Partial<Record<HistorialTab, number | null>>;
}

export function HistorialTabs({ value, onChange, counts }: HistorialTabsProps) {
  return (
    <div role="tablist" className="flex flex-wrap gap-1 border-b border-border">
      {HISTORIAL_TABS.map((tab) => {
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
                  active
                    ? "bg-brand-orange/[.12] text-brand-orange"
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
