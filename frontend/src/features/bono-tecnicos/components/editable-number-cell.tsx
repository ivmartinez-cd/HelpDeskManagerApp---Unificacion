"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/shared/utils/cn";

interface EditableNumberCellProps {
  value: number;
  /** Qué mostrar en el input mientras `value` todavía no tiene nada cargado
   * (ej. el sugerido de días hábiles). El campo se ve prellenado, pero sigue
   * sin persistir nada hasta que el usuario haga foco y blur en la celda —
   * en ese momento se compara igual contra `value`, no contra esto, así que
   * un blur sin tocar nada sí dispara el guardado (confirmación mínima, no
   * autoguardado en cuanto se calcula el sugerido). */
  initialDraft?: number;
  disabled: boolean;
  saving: boolean;
  onCommit: (value: number) => void;
}

/** Input numérico inline de una celda de tabla — commitea con onBlur, solo si
 * el valor cambió (evita un PUT de más al simplemente hacer foco y salir). */
export function EditableNumberCell({
  value,
  initialDraft,
  disabled,
  saving,
  onCommit,
}: EditableNumberCellProps) {
  const [draft, setDraft] = useState(String(initialDraft ?? value));

  // Si el resumen se recarga (guardado de otra celda, cambio de período), el
  // draft local tiene que seguir al valor del servidor — ajustado durante el
  // render, no en un efecto (mismo patrón que use-sla-detail.ts). Ojo: sigue
  // a `value` (lo guardado), no a `initialDraft` (el sugerido) — si no,
  // cualquier cambio de sugerido pisaría lo que el usuario está tipeando.
  const [prevValue, setPrevValue] = useState(value);
  if (value !== prevValue) {
    setPrevValue(value);
    setDraft(String(value));
  }

  const handleBlur = () => {
    const parsed = Number(draft);
    if (!Number.isFinite(parsed) || parsed < 0) {
      setDraft(String(value));
      return;
    }
    // Medios días (ej. 20.5), no cualquier decimal — mismo criterio del backend.
    const normalizado = Math.round(parsed * 2) / 2;
    setDraft(String(normalizado));
    if (normalizado !== value) onCommit(normalizado);
  };

  return (
    <span className="inline-flex items-center gap-1.5">
      <input
        type="number"
        min={0}
        step={0.5}
        value={draft}
        disabled={disabled || saving}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={handleBlur}
        className={cn(
          "w-16 rounded-[8px] border border-border bg-card px-2 py-1 text-right font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40",
          (disabled || saving) && "opacity-60",
        )}
      />
      {saving && <Loader2 className="h-3.5 w-3.5 flex-none animate-spin text-muted-foreground" />}
    </span>
  );
}
