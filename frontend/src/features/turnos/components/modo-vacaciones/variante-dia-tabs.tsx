"use client";

import { Copy } from "lucide-react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import type { FranjaEditable } from "../../types/grilla-variantes";
import { DIAS_SEMANA } from "../../lib/variante-validacion";

interface Props {
  franjas: FranjaEditable[];
  diaActivo: number;
  setDiaActivo: (dia: number) => void;
  hayFranjasDelDia: boolean;
  onCopiarALaborables: () => void;
}

/** Tabs de día de semana + "aplicar a lunes-viernes" del editor de grilla de
 * vacaciones, extraído de `variante-editor.tsx` porque ese archivo ya
 * superaba el tamaño máximo de archivo (§4). */
export function VarianteDiaTabs({
  franjas, diaActivo, setDiaActivo, hayFranjasDelDia, onCopiarALaborables,
}: Props) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 pb-2">
      <div role="tablist" aria-label="Día de semana" className="flex flex-wrap items-center gap-1">
        {DIAS_SEMANA.map((dia, idx) => {
          const cantidad = franjas.filter((f) => f.diaSemana === idx).length;
          return (
            <button
              key={dia}
              type="button"
              role="tab"
              aria-selected={diaActivo === idx}
              onClick={() => setDiaActivo(idx)}
              className={`rounded-[6px] px-3 py-1.5 font-body text-xs font-semibold transition-colors ${
                diaActivo === idx
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              {dia}
              {cantidad > 0 && <span className="ml-1 opacity-70">({cantidad})</span>}
            </button>
          );
        })}
      </div>
      {diaActivo <= 4 && hayFranjasDelDia && (
        <BrandButton type="button" variant="outline" size="sm" onClick={onCopiarALaborables}>
          <Copy className="h-3.5 w-3.5" />
          Aplicar este día a lunes–viernes
        </BrandButton>
      )}
    </div>
  );
}
