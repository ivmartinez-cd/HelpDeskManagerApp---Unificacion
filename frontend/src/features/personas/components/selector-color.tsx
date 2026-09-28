"use client";

interface Props {
  value: string;
  onChange: (color: string) => void;
  disabled?: boolean;
}

/** Selector de color libre (sin paleta fija, pedido de Iván 2026-09-28): el
 * color es uno solo para toda la app (turnos, avatar, calendario). */
export function SelectorColor({ value, onChange, disabled }: Props) {
  return (
    <div>
      <span className="mb-1.5 block font-body text-[13px] font-semibold text-foreground">
        Color de identidad
      </span>
      <input
        type="color"
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        aria-label="Color de identidad"
        className="h-8 w-10 cursor-pointer rounded-[8px] border border-border bg-card p-0.5 disabled:cursor-default"
      />
    </div>
  );
}
