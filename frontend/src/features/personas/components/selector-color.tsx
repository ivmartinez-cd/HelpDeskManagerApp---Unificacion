"use client";

import { COLORES_IDENTIDAD } from "@/features/vacaciones/lib/fechas";

interface Props {
  value: string;
  onChange: (color: string) => void;
  disabled?: boolean;
}

/** Paleta de Gestión de Personal + color libre (el que tenían las cuentas en
 * Usuarios): el color es uno solo para toda la app (turnos, avatar, calendario). */
export function SelectorColor({ value, onChange, disabled }: Props) {
  return (
    <div>
      <span className="mb-1.5 block font-body text-[13px] font-semibold text-foreground">
        Color de identidad
      </span>
      <div className="flex flex-wrap items-center gap-2">
        {COLORES_IDENTIDAD.map((c) => (
          <button
            key={c}
            type="button"
            aria-label={`Color ${c}`}
            disabled={disabled}
            onClick={() => onChange(c)}
            className={
              value.toLowerCase() === c.toLowerCase()
                ? "h-7 w-7 rounded-[8px] ring-2 ring-brand-orange ring-offset-2 ring-offset-background"
                : "h-7 w-7 rounded-[8px] opacity-70 hover:opacity-100 disabled:hover:opacity-70"
            }
            style={{ backgroundColor: c }}
          />
        ))}
        <input
          type="color"
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          title="Otro color"
          aria-label="Otro color"
          className="h-8 w-10 cursor-pointer rounded-[8px] border border-border bg-card p-0.5 disabled:cursor-default"
        />
      </div>
    </div>
  );
}
