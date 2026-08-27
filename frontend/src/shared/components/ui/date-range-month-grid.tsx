"use client";

import { useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { formatPlainDate } from "@/shared/utils/date-arg";
import type { DateRange } from "@/shared/types/date-range";
import { WEEKDAYS, buildMonthCells, toKey } from "./date-range-utils";

/** Piezas de presentación del selector de rango (`date-range-picker.tsx`):
 * un mes de la grilla y el par Desde/Hasta del footer. */

export function RangeEnd({ label, value }: { label: string; value?: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="font-body text-[11px] font-semibold uppercase tracking-[.04em] text-muted-foreground">
        {label}
      </span>
      <span className="font-heading text-sm font-bold text-foreground">{formatPlainDate(value)}</span>
    </div>
  );
}

interface MonthGridProps {
  month: Date;
  draft: DateRange | null;
  pendingStart: string | null;
  isDisabled: (key: string) => boolean;
  onSelect: (key: string) => void;
  onPrev?: () => void;
  onNext?: () => void;
}

export function MonthGrid({
  month,
  draft,
  pendingStart,
  isDisabled,
  onSelect,
  onPrev,
  onNext,
}: MonthGridProps) {
  const cells = useMemo(
    () => buildMonthCells(month.getFullYear(), month.getMonth()),
    [month],
  );
  const label = month.toLocaleDateString("es-AR", { month: "long", year: "numeric" });

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-5">
        {onPrev ? (
          <button
            type="button"
            onClick={onPrev}
            aria-label="Mes anterior"
            className="cursor-pointer rounded-[6px] p-1 text-muted-foreground hover:text-brand-orange"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        ) : (
          <span className="w-6" />
        )}
        <span className="font-heading text-sm font-bold capitalize text-foreground">{label}</span>
        {onNext ? (
          <button
            type="button"
            onClick={onNext}
            aria-label="Mes siguiente"
            className="cursor-pointer rounded-[6px] p-1 text-muted-foreground hover:text-brand-orange"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        ) : (
          <span className="w-6" />
        )}
      </div>

      <div className="grid grid-cols-7 gap-0.5">
        {WEEKDAYS.map((weekday) => (
          <div
            key={weekday}
            className="flex h-7 w-9 items-center justify-center font-body text-[11px] font-semibold text-muted-foreground"
          >
            {weekday}
          </div>
        ))}
        {cells.map((date, index) => {
          if (!date) return <span key={`gap-${index}`} className="h-9 w-9" />;
          const key = toKey(date);
          const isStart = draft?.startDate === key;
          const isEnd = draft?.endDate === key;
          // Con un solo extremo elegido todavía no hay "adentro del rango".
          const inRange =
            !!draft &&
            pendingStart === null &&
            key > draft.startDate &&
            key < draft.endDate;
          const disabled = isDisabled(key);
          return (
            <button
              key={key}
              type="button"
              disabled={disabled}
              onClick={() => onSelect(key)}
              aria-pressed={isStart || isEnd}
              style={{
                borderRadius:
                  isStart && isEnd
                    ? "50%"
                    : isStart
                      ? "50% 0 0 50%"
                      : isEnd
                        ? "0 50% 50% 0"
                        : inRange
                          ? "0"
                          : "50%",
              }}
              className={cn(
                "flex h-9 w-9 items-center justify-center font-body text-[13px] transition-colors",
                disabled ? "cursor-not-allowed text-muted-foreground/40" : "cursor-pointer",
                !disabled && !isStart && !isEnd && !inRange && "text-foreground hover:bg-muted",
                inRange && "bg-brand-orange/[.12] text-brand-orange",
                (isStart || isEnd) && "bg-brand-orange font-bold text-white",
              )}
            >
              {date.getDate()}
            </button>
          );
        })}
      </div>
    </div>
  );
}
