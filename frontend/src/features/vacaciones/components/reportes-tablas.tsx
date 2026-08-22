"use client";

import { Search } from "lucide-react";
import type { FilaEmpleadoReporte, ReporteVacaciones } from "../types/vacaciones";

function iniciales(nombre: string): string {
  return nombre
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join("")
    .toUpperCase();
}

const TH = "px-3.5 py-2.5 text-right font-heading text-[10px] uppercase tracking-[.05em]";

export function TablaEmpleados({
  filas,
  filtro,
  onFiltro,
}: {
  filas: FilaEmpleadoReporte[];
  filtro: string;
  onFiltro: (v: string) => void;
}) {
  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h3 className="font-heading text-[13px] font-bold text-foreground">Por empleado</h3>
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Filtrar…"
            value={filtro}
            onChange={(e) => onFiltro(e.target.value)}
            className="w-40 rounded-[7px] border border-border bg-muted/30 py-1.5 pl-8 pr-3 font-body text-[12.5px] text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-brand-orange/40"
          />
        </div>
      </div>
      <table className="w-full font-body text-[13px]">
        <thead>
          <tr className="border-b border-border bg-muted/30 text-muted-foreground">
            <th className={`${TH} text-left`}>Empleado</th>
            <th className={`${TH} text-[#F7941D]`}>Cons.</th>
            <th className={TH}>Pend.</th>
            <th className={TH}>Disp.</th>
          </tr>
        </thead>
        <tbody>
          {filas.map((f) => (
            <tr key={f.nombre} className="border-b border-border/60 last:border-0">
              <td className="px-3.5 py-2.5">
                <div className="flex items-center gap-2">
                  <div
                    className="flex h-[26px] w-[26px] flex-none items-center justify-center rounded-[6px] font-heading text-[9.5px] font-bold text-white"
                    style={{ backgroundColor: f.color }}
                  >
                    {iniciales(f.nombre)}
                  </div>
                  <span className="font-semibold text-foreground">{f.nombre}</span>
                </div>
              </td>
              <td className="px-3.5 py-2.5 text-right font-semibold text-[#F7941D]">
                {f.used}
              </td>
              <td className="px-3.5 py-2.5 text-right text-[#d97706]">{f.pending}</td>
              <td className="px-3.5 py-2.5 text-right font-semibold text-[#059669]">
                {f.available}
              </td>
            </tr>
          ))}
          {filas.length === 0 && (
            <tr>
              <td colSpan={4} className="px-3.5 py-4 text-center text-muted-foreground">
                Sin resultados para el filtro.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export function TablaSectores({ data }: { data: ReporteVacaciones }) {
  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h3 className="font-heading text-[13px] font-bold text-foreground">Por sector</h3>
      </div>
      <table className="w-full font-body text-[13px]">
        <thead>
          <tr className="border-b border-border bg-muted/30 text-muted-foreground">
            <th className={`${TH} text-left`}>Sector</th>
            <th className={TH}>Empl.</th>
            <th className={TH}>Anuales</th>
            <th className={`${TH} text-[#F7941D]`}>Cons.</th>
            <th className={TH}>Disp.</th>
          </tr>
        </thead>
        <tbody>
          {data.porSector.map((s) => (
            <tr key={s.nombre} className="border-b border-border/60 last:border-0">
              <td className="px-3.5 py-2.5">
                <div className="flex items-center gap-[7px]">
                  <div
                    className="h-2 w-2 flex-none rounded-full"
                    style={{ backgroundColor: s.color }}
                  />
                  <span className="font-semibold text-foreground">{s.nombre}</span>
                </div>
              </td>
              <td className="px-3.5 py-2.5 text-right text-muted-foreground">
                {s.empleados}
              </td>
              <td className="px-3.5 py-2.5 text-right text-muted-foreground">{s.annual}</td>
              <td className="px-3.5 py-2.5 text-right font-semibold text-[#F7941D]">
                {s.used}
              </td>
              <td className="px-3.5 py-2.5 text-right font-semibold text-[#059669]">
                {s.available}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
