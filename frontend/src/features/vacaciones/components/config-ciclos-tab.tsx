"use client";

import { BrandSelect } from "@/shared/components/ui/brand-form";
import type { ConfigVacaciones } from "../types/vacaciones";

interface Props {
  config: ConfigVacaciones;
  onChange: (patch: Partial<ConfigVacaciones>) => void;
}

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

export function ConfigCiclosTab({ config, onChange }: Props) {
  const proximoAnio = new Date().getFullYear() + 1;

  return (
    <div className="flex max-w-[560px] flex-col gap-4">
      <div className="rounded-[12px] border border-border bg-card p-5">
        <h3 className="mb-3.5 font-heading text-sm font-bold text-foreground">
          Apertura del próximo ciclo anual
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <BrandSelect
            label="Día"
            value={String(config.nextYearOpenDay)}
            onChange={(e) => onChange({ nextYearOpenDay: Number(e.target.value) })}
          >
            {Array.from({ length: 31 }, (_, i) => (
              <option key={i + 1} value={String(i + 1)}>
                {i + 1}
              </option>
            ))}
          </BrandSelect>
          <BrandSelect
            label="Mes"
            value={String(config.nextYearOpenMonth)}
            onChange={(e) => onChange({ nextYearOpenMonth: Number(e.target.value) })}
          >
            {MESES.map((m, i) => (
              <option key={m} value={String(i + 1)}>
                {m}
              </option>
            ))}
          </BrandSelect>
        </div>
        <p className="mt-3.5 rounded-[8px] bg-muted/30 px-3.5 py-2.5 font-body text-[12.5px] leading-snug text-muted-foreground">
          El próximo ciclo se abrirá el{" "}
          <strong className="text-foreground">
            {config.nextYearOpenDay} de {MESES[config.nextYearOpenMonth - 1]?.toLowerCase()}{" "}
            de {proximoAnio - 1}
          </strong>{" "}
          para las solicitudes del ciclo {proximoAnio}, y asignará días según los rangos de
          antigüedad vigentes.
        </p>
      </div>

      <div className="rounded-[12px] border border-border bg-card p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="font-heading text-sm font-bold text-foreground">
              Arrastrar días no usados
            </h3>
            <p className="mt-0.5 max-w-[380px] font-body text-[12.5px] leading-snug text-muted-foreground">
              Al iniciar el nuevo ciclo, los días no gozados del ciclo anterior se suman al
              saldo del empleado.
            </p>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={config.allowCarryOver}
            onClick={() => onChange({ allowCarryOver: !config.allowCarryOver })}
            className={`relative mt-0.5 h-[26px] w-[46px] flex-none rounded-full transition-colors ${
              config.allowCarryOver ? "bg-brand-orange" : "bg-muted-foreground/30"
            }`}
          >
            <span
              className={`absolute top-[3px] h-5 w-5 rounded-full bg-white shadow transition-all ${
                config.allowCarryOver ? "left-[23px]" : "left-[3px]"
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
}
