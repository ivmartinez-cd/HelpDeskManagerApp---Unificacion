"use client";

import { X } from "lucide-react";
import type { ConfigVacaciones, SeniorityTier } from "../types/vacaciones";

interface Props {
  config: ConfigVacaciones;
  onChange: (patch: Partial<ConfigVacaciones>) => void;
}

const inputClass =
  "w-20 rounded-[7px] border border-border bg-muted/20 px-3 py-2 text-center font-body text-sm font-semibold text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40";

export function ConfigAntiguedadTab({ config, onChange }: Props) {
  const tiers = config.seniorityTiers;

  const setTier = (i: number, patch: Partial<SeniorityTier>) => {
    onChange({
      seniorityTiers: tiers.map((t, j) => (j === i ? { ...t, ...patch } : t)),
    });
  };

  const quitar = (i: number) => {
    onChange({ seniorityTiers: tiers.filter((_, j) => j !== i) });
  };

  const agregar = () => {
    const ultimo = tiers[tiers.length - 1];
    onChange({
      seniorityTiers: [
        ...tiers,
        { minYears: ultimo?.maxYears ?? 0, maxYears: (ultimo?.maxYears ?? 0) + 5, days: 20 },
      ],
    });
  };

  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="border-b border-border px-5 py-4">
        <h3 className="font-heading text-sm font-bold text-foreground">
          Rangos de antigüedad y días de vacaciones
        </h3>
        <p className="mt-0.5 font-body text-[12.5px] text-muted-foreground">
          Los días se asignan automáticamente al ciclo según los años de antigüedad del
          empleado.
        </p>
      </div>
      <table className="w-full font-body text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/30 text-left font-heading text-[10.5px] uppercase tracking-[.05em] text-muted-foreground">
            <th className="px-5 py-2.5">Desde (años)</th>
            <th className="px-5 py-2.5">Hasta (años)</th>
            <th className="px-5 py-2.5">Días de vacaciones</th>
            <th className="w-12 px-5 py-2.5" />
          </tr>
        </thead>
        <tbody>
          {tiers.map((t, i) => (
            <tr key={i} className="border-b border-border/60 last:border-0">
              <td className="px-5 py-2.5">
                <input
                  type="number"
                  min={0}
                  step={0.5}
                  value={t.minYears}
                  onChange={(e) => setTier(i, { minYears: Number(e.target.value) })}
                  className={inputClass}
                />
              </td>
              <td className="px-5 py-2.5">
                <input
                  type="number"
                  min={0}
                  step={0.5}
                  value={t.maxYears}
                  onChange={(e) => setTier(i, { maxYears: Number(e.target.value) })}
                  className={inputClass}
                />
              </td>
              <td className="px-5 py-2.5">
                <span className="flex items-center gap-2">
                  <input
                    type="number"
                    min={1}
                    max={365}
                    value={t.days}
                    onChange={(e) => setTier(i, { days: Number(e.target.value) })}
                    className={`${inputClass} font-bold text-brand-orange`}
                  />
                  <span className="text-[13px] text-muted-foreground">días</span>
                </span>
              </td>
              <td className="px-5 py-2.5">
                <button
                  type="button"
                  onClick={() => quitar(i)}
                  disabled={tiers.length <= 1}
                  aria-label="Eliminar rango"
                  className="flex h-7 w-7 items-center justify-center rounded-[6px] border border-destructive/20 text-destructive hover:bg-destructive/10 disabled:opacity-40"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="border-t border-border px-5 py-3.5">
        <button
          type="button"
          onClick={agregar}
          className="rounded-[7px] border-[1.5px] border-dashed border-brand-orange/40 bg-brand-orange/5 px-4 py-1.5 font-body text-[13px] font-semibold text-brand-orange hover:bg-brand-orange/10"
        >
          + Agregar rango
        </button>
      </div>
    </div>
  );
}
