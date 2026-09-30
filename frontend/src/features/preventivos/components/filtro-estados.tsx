"use client";

import type { EstadoPreventivo } from "../types/preventivos";
import { cn } from "@/shared/utils/cn";

const ESTADOS: { value: EstadoPreventivo; label: string }[] = [
  { value: "vencido", label: "Vencidos" },
  { value: "por_vencer", label: "Por vencer" },
  { value: "al_dia", label: "Al día" },
  { value: "sin_preventivo", label: "Sin preventivo" },
];

/** Mismo aspecto que `SegmentedControl`, pero multi-selección: cada estado se
 * prende/apaga solo; "Todos" limpia la selección (vacío = sin filtro). */
export function FiltroEstados({
  value,
  onChange,
}: {
  value: EstadoPreventivo[];
  onChange: (value: EstadoPreventivo[]) => void;
}) {
  const opciones = [{ value: null, label: "Todos" }, ...ESTADOS];
  return (
    <div
      role="group"
      aria-label="Estado"
      className="inline-flex w-fit items-center gap-0.5 rounded-[10px] border border-border bg-muted p-0.5"
    >
      {opciones.map((opcion) => {
        const activo = opcion.value === null ? value.length === 0 : value.includes(opcion.value);
        const alternar = () => {
          if (opcion.value === null) return onChange([]);
          const estado = opcion.value;
          onChange(activo ? value.filter((v) => v !== estado) : [...value, estado]);
        };
        return (
          <button
            key={opcion.label}
            type="button"
            aria-pressed={activo}
            onClick={alternar}
            className={cn(
              "rounded-[8px] px-2.5 py-1 font-body text-xs font-semibold outline-none transition-colors focus-visible:ring-2 focus-visible:ring-brand-orange/40",
              activo
                ? "bg-card text-brand-orange shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {opcion.label}
          </button>
        );
      })}
    </div>
  );
}
