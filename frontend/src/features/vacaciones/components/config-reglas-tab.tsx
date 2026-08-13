"use client";

import { Minus, Plus } from "lucide-react";
import type { ConfigVacaciones } from "../types/vacaciones";

interface Props {
  config: ConfigVacaciones;
  onChange: (patch: Partial<ConfigVacaciones>) => void;
}

function Stepper({
  value,
  onChange,
  min = 0,
}: {
  value: number;
  onChange: (v: number) => void;
  min?: number;
}) {
  return (
    <span className="flex items-center overflow-hidden rounded-[8px] border border-border">
      <button
        type="button"
        onClick={() => onChange(Math.max(min, value - 1))}
        aria-label="Restar"
        className="flex h-10 w-9 items-center justify-center bg-muted/30 text-foreground hover:bg-muted"
      >
        <Minus className="h-4 w-4" />
      </button>
      <span className="flex h-10 min-w-[52px] items-center justify-center border-x border-border px-3 font-heading text-lg font-bold text-foreground">
        {value}
      </span>
      <button
        type="button"
        onClick={() => onChange(value + 1)}
        aria-label="Sumar"
        className="flex h-10 w-9 items-center justify-center bg-muted/30 text-foreground hover:bg-muted"
      >
        <Plus className="h-4 w-4" />
      </button>
    </span>
  );
}

export function ConfigReglasTab({ config, onChange }: Props) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-[12px] border border-border bg-card p-5">
        <h3 className="font-heading text-sm font-bold text-foreground">
          Aviso Previo Mínimo
        </h3>
        <p className="mb-4 mt-0.5 font-body text-[12.5px] leading-snug text-muted-foreground">
          Días hábiles de anticipación mínimos que el empleado debe respetar al crear una
          solicitud.
        </p>
        <div className="flex items-center gap-3">
          <Stepper
            value={config.minAdvanceNoticeDays}
            onChange={(v) => onChange({ minAdvanceNoticeDays: v })}
          />
          <span className="font-body text-[13.5px] text-muted-foreground">días hábiles</span>
        </div>
      </div>

      <div className="rounded-[12px] border border-border bg-card p-5">
        <h3 className="font-heading text-sm font-bold text-foreground">
          Límite de Solapamiento
        </h3>
        <p className="mb-4 mt-0.5 font-body text-[12.5px] leading-snug text-muted-foreground">
          Porcentaje máximo de empleados del sector que pueden estar de vacaciones
          simultáneamente.
        </p>
        <div className="mb-2 flex items-center justify-between">
          <span className="font-body text-[13px] text-muted-foreground">
            Máximo del equipo
          </span>
          <span className="font-heading text-base font-bold text-brand-orange">
            {config.maxOverlapPercent}%
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={100}
          value={config.maxOverlapPercent}
          onChange={(e) => onChange({ maxOverlapPercent: Number(e.target.value) })}
          className="w-full accent-brand-orange"
        />
        <div className="mt-4 flex items-center gap-3">
          <span className="flex-1 font-body text-[13px] text-muted-foreground">
            Cantidad fija máxima{" "}
            <span className="text-muted-foreground/70">(0 = usar %)</span>
          </span>
          <Stepper
            value={config.maxOverlapCount}
            onChange={(v) => onChange({ maxOverlapCount: v })}
          />
        </div>
      </div>
    </div>
  );
}
