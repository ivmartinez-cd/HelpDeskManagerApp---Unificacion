"use client";

import { Trash2 } from "lucide-react";
import type { FranjaEditable } from "../../types/grilla-variantes";
import { SearchableSelect, type SearchableSelectOption } from "@/shared/components/ui/searchable-select";
import { cn } from "@/shared/utils/cn";

interface VarianteFranjaFilaProps {
  franja: FranjaEditable;
  casillaNombre: string;
  operadores: SearchableSelectOption[];
  conError: boolean;
  onChange: (cambios: Partial<FranjaEditable>) => void;
  onRemove: () => void;
}

const inputHoraClass =
  "w-[104px] rounded-[8px] border border-border bg-card px-2.5 py-[7px] font-mono text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40";

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
      <label className="flex flex-col gap-1 font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
        Inicio
        <input
          type="time"
          aria-label={`Inicio ${etiqueta}`}
          value={franja.horaInicio}
          onChange={(e) => onChange({ horaInicio: e.target.value })}
          className={inputHoraClass}
        />
      </label>
      <label className="flex flex-col gap-1 font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
        Fin
        <input
          type="time"
          aria-label={`Fin ${etiqueta}`}
          value={franja.horaFin}
          onChange={(e) => onChange({ horaFin: e.target.value })}
          className={inputHoraClass}
        />
      </label>
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
