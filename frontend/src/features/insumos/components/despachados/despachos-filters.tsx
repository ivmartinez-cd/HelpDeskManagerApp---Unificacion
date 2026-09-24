"use client";

import { useId } from "react";
import { Search } from "lucide-react";
import { DateRangePickerPopover } from "@/shared/components/ui/date-range-picker-popover";
import type { DateRange } from "@/shared/types/date-range";

/** Barra de filtros de "Todos los despachos" (presentacional: el estado vive
 * en la vista y lo aplica el backend en SQL). */

const LABEL = "font-body text-[11px] font-bold uppercase leading-[1.4] tracking-[.025em] text-muted-foreground";
const CONTROL =
  "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-[13px] leading-[18px] text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40";

interface Props {
  texto: string;
  onTexto: (v: string) => void;
  operativa: string;
  onOperativa: (v: string) => void;
  operativas: string[];
  rango: DateRange | null;
  onRango: (r: DateRange | null) => void;
  onLimpiar: () => void;
}

export function DespachosFilters(props: Props) {
  const id = useId();
  return (
    <div role="search" className="flex flex-wrap items-end gap-3 border-b border-border px-5 py-3.5">
      <div className="relative flex min-w-[220px] flex-[1_1_280px] flex-col gap-[5px]">
        <label htmlFor={`${id}-q`} className={LABEL}>Buscar</label>
        <input
          id={`${id}-q`}
          type="search"
          autoComplete="off"
          value={props.texto}
          onChange={(e) => props.onTexto(e.target.value)}
          placeholder="Guía, cliente, incidente o remito"
          maxLength={100}
          className={`${CONTROL} w-full pl-[34px] placeholder:text-muted-foreground`}
        />
        <Search className="pointer-events-none absolute bottom-[10px] left-[11px] h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
      </div>
      <div className="flex flex-col gap-[5px]">
        <label htmlFor={`${id}-op`} className={LABEL}>Operativa</label>
        <select id={`${id}-op`} value={props.operativa} onChange={(e) => props.onOperativa(e.target.value)} className={CONTROL}>
          <option value="">Todas</option>
          {props.operativas.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      </div>
      <div className="flex flex-col gap-[5px]">
        <span id={`${id}-fechas`} className={LABEL}>Fecha de remito</span>
        <div role="group" aria-labelledby={`${id}-fechas`}>
          <DateRangePickerPopover value={props.rango} onChange={props.onRango} placeholder="Cualquier fecha" />
        </div>
      </div>
      <button
        type="button"
        onClick={props.onLimpiar}
        className="cursor-pointer self-end rounded-[6px] px-1 py-2 font-body text-[13px] font-bold text-[#b45f06] hover:underline focus-visible:outline-2 focus-visible:outline-brand-orange dark:text-brand-orange"
      >
        Limpiar filtros
      </button>
    </div>
  );
}
