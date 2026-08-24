"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/shared/utils/cn";

interface EditableNumberCellProps {
  value: number;
  disabled: boolean;
  saving: boolean;
  onCommit: (value: number) => void;
}

/** Input numérico inline de una celda de tabla — commitea con onBlur, solo si
 * el valor cambió (evita un PUT de más al simplemente hacer foco y salir). */
export function EditableNumberCell({ value, disabled, saving, onCommit }: EditableNumberCellProps) {
  const [draft, setDraft] = useState(String(value));

  // Si el resumen se recarga (guardado de otra celda, cambio de período), el
  // draft local tiene que seguir al valor del servidor — ajustado durante el
  // render, no en un efecto (mismo patrón que use-sla-detail.ts).
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
    const normalizado = Math.trunc(parsed);
    setDraft(String(normalizado));
    if (normalizado !== value) onCommit(normalizado);
  };

  return (
    <span className="inline-flex items-center gap-1.5">
      <input
        type="number"
        min={0}
        step={1}
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
