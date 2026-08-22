"use client";

import type { ReporteVacaciones } from "../types/vacaciones";

const ALTO_MAX_BARRA = 150;

export function GraficoSectores({ data }: { data: ReporteVacaciones }) {
  const hoy = new Date().toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
  const max = Math.max(1, ...data.porSector.flatMap((s) => [s.used, s.available]));
  const alto = (v: number) => Math.round((v / max) * ALTO_MAX_BARRA);
  return (
    <div className="rounded-[12px] border border-border bg-card p-[22px]">
      <h3 className="font-heading text-sm font-bold text-foreground">
        Días consumidos vs. disponibles por sector
      </h3>
      <p className="mb-5 mt-1 font-body text-[12.5px] text-muted-foreground">
        Ciclo {data.year} — actualizado al {hoy}
      </p>
      <div className="mb-3.5 flex h-[180px] items-end justify-center gap-7 border-b border-border px-5">
        {data.porSector.map((s) => (
          <div key={s.nombre} className="flex flex-col items-center gap-1.5">
            <div className="flex h-40 items-end gap-1">
              <div className="flex flex-col items-center justify-end gap-0.5">
                <span className="font-body text-[10px] font-semibold text-[#F7941D]">
                  {s.used}
                </span>
                <div
                  className="w-[26px] rounded-t-[4px] bg-[#F7941D]"
                  style={{ height: `${alto(s.used)}px` }}
                />
              </div>
              <div className="flex flex-col items-center justify-end gap-0.5">
                <span className="font-body text-[10px] font-semibold text-muted-foreground">
                  {s.available}
                </span>
                <div
                  className="w-[26px] rounded-t-[4px] bg-muted"
                  style={{ height: `${alto(s.available)}px` }}
                />
              </div>
            </div>
            <span className="max-w-[80px] text-center font-body text-[11.5px] text-muted-foreground">
              {s.nombre}
            </span>
          </div>
        ))}
      </div>
      <div className="flex justify-center gap-[18px]">
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded-[3px] bg-[#F7941D]" />
          <span className="font-body text-[12.5px] text-muted-foreground">Consumidos</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded-[3px] bg-muted" />
          <span className="font-body text-[12.5px] text-muted-foreground">Disponibles</span>
        </div>
      </div>
    </div>
  );
}
