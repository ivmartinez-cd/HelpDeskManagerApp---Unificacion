"use client";

import { BrandButton } from "@/shared/components/ui/brand-form";

/** Fila de acciones al pie de cada paso opcional: Saltear a la izquierda,
 * acción primaria del paso a la derecha. Los pasos usan `onClick` directo en
 * vez de `<form onSubmit>` porque conviven varios botones con semántica
 * distinta (saltear ≠ confirmar) en el mismo pie. */
export function PasoAcciones({
  onSaltear,
  primario,
  primarioTexto,
  primarioDisabled,
  saving,
}: {
  onSaltear: () => void;
  primario?: () => void;
  primarioTexto?: string;
  primarioDisabled?: boolean;
  saving?: boolean;
}) {
  return (
    <div className="flex justify-end gap-2 pt-1">
      <BrandButton type="button" variant="outline" onClick={onSaltear}>
        Saltear
      </BrandButton>
      {primario && primarioTexto && (
        <BrandButton type="button" loading={saving} disabled={primarioDisabled} onClick={primario}>
          {primarioTexto}
        </BrandButton>
      )}
    </div>
  );
}
