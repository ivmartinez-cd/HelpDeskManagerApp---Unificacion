"use client";

import { Calendar } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  type DateFilter,
  type DateFilterRange,
  PRESET_OPTIONS,
  dateFilterLabel,
} from "../utils/date-filter";

interface Props {
  value: DateFilter;
  onChange: (filter: DateFilter) => void;
}

export function DateRangePicker({ value, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  function applyCustomRange() {
    if (!customStart) return;
    const range: DateFilterRange = { start: customStart, end: customEnd || customStart };
    onChange(range);
    setOpen(false);
  }

  return (
    <div ref={ref} className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 rounded-[8px] border border-border bg-card px-3 py-2 font-body text-[12px] text-muted-foreground hover:text-foreground transition-colors"
      >
        <Calendar className="h-3.5 w-3.5" />
        {dateFilterLabel(value)}
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-1 flex w-[280px] flex-col gap-2 rounded-[10px] border border-border bg-card p-3 shadow-lg">
          <div className="flex flex-col gap-1">
            {PRESET_OPTIONS.map((p) => (
              <button
                key={p.value}
                type="button"
                onClick={() => {
                  onChange(p.value);
                  setOpen(false);
                }}
                className="rounded-[6px] px-2 py-1.5 text-left font-body text-[12px] text-foreground hover:bg-white/[.05] transition-colors"
              >
                {p.label}
              </button>
            ))}
          </div>
          <div className="border-t border-border pt-2 flex flex-col gap-2">
            <span className="font-body text-[10px] font-bold uppercase tracking-[.05em] text-muted-foreground">
              Rango personalizado
            </span>
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={customStart}
                onChange={(e) => setCustomStart(e.target.value)}
                className="w-full rounded-[6px] border border-border bg-background px-2 py-1 font-body text-[12px] text-foreground"
              />
              <span className="text-muted-foreground">–</span>
              <input
                type="date"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
                className="w-full rounded-[6px] border border-border bg-background px-2 py-1 font-body text-[12px] text-foreground"
              />
            </div>
            <button
              type="button"
              onClick={applyCustomRange}
              disabled={!customStart}
              className="rounded-[6px] bg-brand-orange px-2 py-1.5 font-body text-[12px] font-semibold text-black disabled:opacity-50"
            >
              Aplicar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
