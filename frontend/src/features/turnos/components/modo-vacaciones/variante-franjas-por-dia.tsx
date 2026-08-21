"use client";

import { Plus } from "lucide-react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import type { SearchableSelectOption } from "@/shared/components/ui/searchable-select";
import type { Casilla } from "../../types/turnos";
import type { FranjaEditable } from "../../types/grilla-variantes";
import { VarianteFranjaFila } from "./variante-franja-fila";

interface Props {
  casillas: Casilla[];
  diaLabel: string;
  franjasDelDia: FranjaEditable[];
  opcionesOperador: SearchableSelectOption[];
  keysConError: Set<string>;
  onAgregar: (casillaId: string) => void;
  onActualizar: (key: string, cambios: Partial<FranjaEditable>) => void;
  onEliminar: (key: string) => void;
}

/** Franjas del día activo, agrupadas por casilla — extraído de
 * `variante-editor.tsx` porque ese archivo ya superaba el tamaño máximo de
 * archivo (§4). */
export function VarianteFranjasPorDia({
  casillas, diaLabel, franjasDelDia, opcionesOperador, keysConError,
  onAgregar, onActualizar, onEliminar,
}: Props) {
  return (
    <div className="flex flex-col gap-4">
      {casillas.map((casilla) => {
        const filas = franjasDelDia
          .filter((f) => f.casillaId === casilla.id)
          .sort((a, b) => a.horaInicio.localeCompare(b.horaInicio));
        return (
          <div key={casilla.id} className="flex flex-col gap-2" data-testid={`casilla-${casilla.nombre}`}>
            <div className="flex items-center justify-between">
              <span className="font-heading text-sm font-bold text-foreground">
                {casilla.nombre} · {diaLabel}
              </span>
              <BrandButton type="button" variant="outline" size="sm" onClick={() => onAgregar(casilla.id)}>
                <Plus className="h-3.5 w-3.5" />
                Agregar franja en {casilla.nombre}
              </BrandButton>
            </div>
            {filas.length === 0 ? (
              <p className="rounded-[10px] border border-dashed border-border px-4 py-3 font-body text-xs text-muted-foreground">
                Sin franjas para {casilla.nombre} este día.
              </p>
            ) : (
              filas.map((f) => (
                <VarianteFranjaFila
                  key={f.key}
                  franja={f}
                  casillaNombre={casilla.nombre}
                  operadores={opcionesOperador}
                  conError={keysConError.has(f.key)}
                  onChange={(cambios) => onActualizar(f.key, cambios)}
                  onRemove={() => onEliminar(f.key)}
                />
              ))
            )}
          </div>
        );
      })}
    </div>
  );
}
