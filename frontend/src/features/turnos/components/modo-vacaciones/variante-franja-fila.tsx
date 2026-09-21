"use client";

import { Trash2 } from "lucide-react";
import type { FranjaEditable } from "../../types/grilla-variantes";
import { SearchableSelect, type SearchableSelectOption } from "@/shared/components/ui/searchable-select";
import { TimeInput } from "@/shared/components/ui/time-input";
import { cn } from "@/shared/utils/cn";

interface VarianteFranjaFilaProps {
  franja: FranjaEditable;
  casillaNombre: string;
  operadores: SearchableSelectOption[];
  conError: boolean;
  onChange: (cambios: Partial<FranjaEditable>) => void;
  onRemove: () => void;
}

/** Una franja del editor: re-cortar límites (inputs time), asignar operadores
 * (mismo catálogo que GET /users) y eliminar. `requiereCobertura` resalta
 * las franjas que la precarga marcó como del ausente. */
export function VarianteFranjaFila({
  franja,
  casillaNombre,
  operadores,
  conError,
  onChange,
  onRemove,
}: VarianteFranjaFilaProps) {
  const etiqueta = `${casillaNombre} ${franja.horaInicio || "--:--"}–${franja.horaFin || "--:--"}`;
  return (
    <div
      data-testid="franja-fila"
      data-requiere-cobertura={franja.requiereCobertura || undefined}
      className={cn(
        "flex flex-wrap items-end gap-3 rounded-[10px] border px-3 py-2.5",
        conError
          ? "border-destructive/40 bg-destructive/5"
          : franja.requiereCobertura && franja.userIds.length === 0
            ? "border-brand-orange/40 bg-brand-orange/5"
            : "border-border bg-card",
      )}
    >
      <TimeInput
        label="Inicio"
        aria-label={`Inicio ${etiqueta}`}
        value={franja.horaInicio}
        onChange={(horaInicio) => onChange({ horaInicio })}
      />
      <TimeInput
        label="Fin"
        aria-label={`Fin ${etiqueta}`}
        value={franja.horaFin}
        onChange={(horaFin) => onChange({ horaFin })}
      />
      <div className="min-w-[260px] flex-1">
        <SearchableSelect
          multiple
          label={`Operadores ${etiqueta}`}
          options={operadores}
          value={franja.userIds}
          onChange={(userIds) => onChange({ userIds })}
          placeholder={franja.requiereCobertura ? "Hueco a cubrir — elegí quién…" : "Elegí operadores…"}
        />
      </div>
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Eliminar franja ${etiqueta}`}
        title="Eliminar franja"
        className="rounded-[8px] p-2 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  );
}
