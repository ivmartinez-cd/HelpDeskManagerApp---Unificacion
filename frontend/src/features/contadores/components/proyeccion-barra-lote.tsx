"use client";

import { BrandButton } from "@/shared/components/ui/brand-form";

/** Barra de acciones en lote ("N seleccionadas") — extraída de `ProyeccionView`
 * para no pasar el máximo de 300 líneas (ARCHITECTURE_GUIDE.md §4). */

interface ProyeccionBarraLoteProps {
  cantidad: number;
  aceptando: boolean;
  onAceptar: () => void;
  onCancelar: () => void;
}

export function ProyeccionBarraLote({ cantidad, aceptando, onAceptar, onCancelar }: ProyeccionBarraLoteProps) {
  if (cantidad === 0) return null;
  return (
    <div className="flex items-center gap-3 rounded-[8px] border border-brand-orange/40 bg-brand-orange/10 px-4 py-2.5">
      <span className="text-sm font-semibold text-foreground">
        {cantidad} seleccionada{cantidad === 1 ? "" : "s"}
      </span>
      <BrandButton loading={aceptando} onClick={onAceptar}>
        Aceptar seleccionadas
      </BrandButton>
      <button
        type="button"
        onClick={onCancelar}
        className="text-xs font-semibold text-muted-foreground hover:text-foreground"
      >
        Cancelar selección
      </button>
    </div>
  );
}
