"use client";

import { useEffect, useRef, useState } from "react";
import { CalendarDays } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { formatPlainDate } from "../../utils/format";
import { DateRangePicker, type DateRangePickerProps } from "./date-range-picker";

interface DateRangePickerPopoverProps extends Omit<DateRangePickerProps, "onApply"> {
  /** Texto del trigger cuando no hay rango elegido. */
  placeholder?: string;
}

/** Trigger compacto + popover con el Patrón 4 adentro — la forma en que lo
 * usan Dashboard, Historial y Estadísticas (barra de acciones). Cierra con
 * click afuera, Escape, o al Aplicar/Limpiar. */
export function DateRangePickerPopover({
  value,
  onChange,
  placeholder = "Rango de fechas",
  className,
  ...pickerProps
}: DateRangePickerPopoverProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const label = value
    ? `${formatPlainDate(value.startDate)} – ${formatPlainDate(value.endDate)}`
    : placeholder;

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        className={cn(
          "flex cursor-pointer items-center gap-2 rounded-[8px] border border-border bg-card px-3.5 py-2.5 font-body text-sm transition-colors hover:bg-muted",
          value ? "font-semibold text-foreground" : "text-muted-foreground",
        )}
      >
        <CalendarDays className="h-4 w-4 flex-none text-brand-orange" aria-hidden="true" />
        {label}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 rounded-[12px] bg-card shadow-[0_20px_60px_rgba(0,0,0,.25)]">
          <DateRangePicker
            {...pickerProps}
            value={value}
            onChange={onChange}
            onApply={() => setOpen(false)}
          />
        </div>
      )}
    </div>
  );
}
