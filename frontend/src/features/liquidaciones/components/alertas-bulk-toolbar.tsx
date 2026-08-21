"use client";

import { X } from "lucide-react";
import { BrandButton } from "@/shared/components/ui/brand-form";

export function AlertasBulkToolbar({
  seleccionadas,
  elegiblesRevisar,
  elegiblesResolver,
  elegiblesDescartar,
  aplicando,
  onRevisar,
  onResolver,
  onDescartar,
  onLimpiar,
}: {
  seleccionadas: number;
  elegiblesRevisar: number;
  elegiblesResolver: number;
  elegiblesDescartar: number;
  aplicando: boolean;
  onRevisar: () => void;
  onResolver: () => void;
  onDescartar: () => void;
  onLimpiar: () => void;
}) {
  if (seleccionadas === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-[10px] border border-brand-orange/30 bg-brand-orange/5 px-4 py-2.5">
      <button
        type="button"
        onClick={onLimpiar}
        title="Cancelar selección"
        className="rounded-full p-0.5 text-muted-foreground hover:text-foreground"
      >
        <X className="h-4 w-4" />
      </button>
      <span className="font-body text-sm font-semibold text-foreground">
        {seleccionadas.toLocaleString("es-AR")} alerta{seleccionadas === 1 ? "" : "s"} seleccionada
        {seleccionadas === 1 ? "" : "s"}
      </span>
      <div className="ml-auto flex flex-wrap gap-2">
        <BrandButton
          variant="outline"
          size="sm"
          disabled={elegiblesRevisar === 0 || aplicando}
          onClick={onRevisar}
        >
          Revisar ({elegiblesRevisar})
        </BrandButton>
        <BrandButton
          variant="outline"
          size="sm"
          disabled={elegiblesResolver === 0 || aplicando}
          onClick={onResolver}
        >
          Resolver ({elegiblesResolver})
        </BrandButton>
        <BrandButton
          size="sm"
          disabled={elegiblesDescartar === 0 || aplicando}
          onClick={onDescartar}
        >
          Descartar ({elegiblesDescartar})
        </BrandButton>
      </div>
    </div>
  );
}
