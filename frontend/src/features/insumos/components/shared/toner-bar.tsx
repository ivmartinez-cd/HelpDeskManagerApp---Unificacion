import { cn } from "@/shared/utils/cn";
import { EMPTY_VALUE } from "../../utils/format";

/** Barra de nivel de tóner del Patrón 1 del handoff.
 *
 * Umbrales de color (fijos, salen del handoff — no son los umbrales de días
 * configurables del backend): verde >30%, naranja 10–30%, rojo <10%.
 *
 * `size="sm"` es la barra de la fila expandida (6px de alto, radio 4px);
 * `size="lg"` es la del modal de detalle de consumible (12px / radio 6px).
 */
export type TonerBarSize = "sm" | "lg";

/** Color de la barra para un nivel dado, expuesto aparte porque el mismo
 * criterio se usa para pintar el número al lado de la barra. */
export function tonerLevelColor(percent: number): string {
  if (percent < 10) return "#ef4444";
  if (percent <= 30) return "#F7941D";
  return "#22c55e";
}

interface TonerBarProps {
  /** Nivel en % (0–100). `null`/`undefined` = sin lectura: barra vacía. */
  percent: number | null | undefined;
  size?: TonerBarSize;
  /** Muestra el número a la derecha de la barra. */
  showValue?: boolean;
  className?: string;
}

export function TonerBar({ percent, size = "sm", showValue = false, className }: TonerBarProps) {
  const hasValue = percent !== null && percent !== undefined && !Number.isNaN(percent);
  const clamped = hasValue ? Math.max(0, Math.min(100, percent)) : 0;
  const trackClass = size === "lg" ? "h-[12px] rounded-[6px]" : "h-[6px] rounded-[4px]";

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div
        role="progressbar"
        aria-valuenow={hasValue ? Math.round(clamped) : undefined}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Nivel de tóner"
        className={cn("min-w-[60px] flex-1 overflow-hidden bg-black/10 dark:bg-white/10", trackClass)}
      >
        {hasValue && (
          <div
            className="h-full transition-[width]"
            style={{
              width: `${clamped}%`,
              background: tonerLevelColor(clamped),
              borderRadius: "inherit",
            }}
          />
        )}
      </div>
      {showValue && (
        <span
          className="w-9 flex-none text-right font-body text-xs font-bold tabular-nums"
          style={hasValue ? { color: tonerLevelColor(clamped) } : undefined}
        >
          {hasValue ? `${Math.round(clamped)}%` : EMPTY_VALUE}
        </span>
      )}
    </div>
  );
}
