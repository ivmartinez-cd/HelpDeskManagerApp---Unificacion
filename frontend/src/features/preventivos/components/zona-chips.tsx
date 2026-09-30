"use client";

import type { ZonaParque } from "../types/preventivos";
import { cn } from "@/shared/utils/cn";
import { numberFormat } from "./preventivos-format";

export function ZonaChips({
  zonas,
  seleccionadas,
  onToggle,
}: {
  zonas: ZonaParque[];
  seleccionadas: string[];
  onToggle: (zona: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Zonas de distribución">
      {zonas.map((z) => {
        const activa = seleccionadas.includes(z.zona);
        return (
          <button
            key={z.zona}
            type="button"
            aria-pressed={activa}
            onClick={() => onToggle(z.zona)}
            className={cn(
              "rounded-full border px-3.5 py-1.5 font-body text-xs font-bold transition-colors",
              activa
                ? "border-brand-orange bg-brand-orange/10 text-brand-orange"
                : "border-border bg-card text-muted-foreground hover:text-foreground",
            )}
          >
            {z.zona}
            <span className={cn("ml-1.5 font-semibold tabular-nums", !activa && "opacity-60")}>
              {numberFormat.format(z.maquinas_activas)}
            </span>
          </button>
        );
      })}
    </div>
  );
}
