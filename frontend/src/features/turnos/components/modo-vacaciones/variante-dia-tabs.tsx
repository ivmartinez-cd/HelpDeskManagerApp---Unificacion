"use client";

import { Copy } from "lucide-react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import type { FranjaEditable } from "../../types/grilla-variantes";
import { DIAS_SEMANA } from "../../lib/variante-validacion";

interface Props {
  franjas: FranjaEditable[];
  diaActivo: number;
  setDiaActivo: (dia: number) => void;
  /** Días que el rango de vigencia alcanza; undefined = una semana o más, todos. */
  diasActivos?: Set<number>;
  hayFranjasDelDia: boolean;
  onCopiarALaborables: () => void;
}

/** Tabs de día de semana + "aplicar a lunes-viernes" del editor de grilla de
 * vacaciones, extraído de `variante-editor.tsx` porque ese archivo ya
 * superaba el tamaño máximo de archivo (§4). */
export function VarianteDiaTabs({
  franjas, diaActivo, setDiaActivo, diasActivos, hayFranjasDelDia, onCopiarALaborables,
}: Props) {
  const aplica = (dia: number) => !diasActivos || diasActivos.has(dia);
  const laborablesDelRango = [0, 1, 2, 3, 4].filter(aplica);
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 pb-2">
      <div role="tablist" aria-label="Día de semana" className="flex flex-wrap items-center gap-1">
        {DIAS_SEMANA.map((dia, idx) => {
          const cantidad = franjas.filter((f) => f.diaSemana === idx).length;
          const fueraDelRango = !aplica(idx);
          return (
            <button
              key={dia}
              type="button"
              role="tab"
              aria-selected={diaActivo === idx}
              disabled={fueraDelRango}
              title={fueraDelRango ? "El rango de vigencia no incluye este día" : undefined}
              onClick={() => setDiaActivo(idx)}
              className={`rounded-[6px] px-3 py-1.5 font-body text-xs font-semibold transition-colors ${
                diaActivo === idx
                  ? "bg-primary text-primary-foreground"
                  : fueraDelRango
                    ? "cursor-not-allowed text-muted-foreground/40"
                    : "text-muted-foreground hover:bg-muted"
              }`}
            >
              {dia}
              {cantidad > 0 && !fueraDelRango && <span className="ml-1 opacity-70">({cantidad})</span>}
            </button>
          );
        })}
      </div>
      {diaActivo <= 4 && hayFranjasDelDia && laborablesDelRango.length > 1 && (
        <BrandButton type="button" variant="outline" size="sm" onClick={onCopiarALaborables}>
          <Copy className="h-3.5 w-3.5" />
          {laborablesDelRango.length === 5
            ? "Aplicar este día a lunes–viernes"
            : `Aplicar este día a ${laborablesDelRango.map((d) => DIAS_SEMANA[d]).join(", ").toLowerCase()}`}
        </BrandButton>
      )}
    </div>
  );
}
