"use client";

import { Tooltip } from "@/shared/components/ui/tooltip";
import {
  coberturaBadgeText,
  formatPillText,
  getPillVisual,
  WEEKDAYS,
} from "../utils/calendario-format";
import type { CalendarEvent, CalendarioVerPor } from "../types/calendario";
import { CoberturaEventoTooltip } from "./cobertura-evento-tooltip";

export interface GridDay {
  dateStr: string;
  dayNum: number;
  isCurrentMonth: boolean;
  isToday: boolean;
}

interface Props {
  gridDays: GridDay[];
  eventsByDayMap: Map<string, CalendarEvent[]>;
  onSelectEvent: (evt: CalendarEvent) => void;
  verPor: CalendarioVerPor;
}

function EventPill({
  evt,
  verPor,
  onSelect,
}: {
  evt: CalendarEvent;
  verPor: CalendarioVerPor;
  onSelect: () => void;
}) {
  const { className, style } = getPillVisual(evt, verPor);
  const displayLabel = formatPillText(evt);
  const cobertura = evt.cobertura;

  const pill = (
    <div
      onClick={onSelect}
      title={cobertura ? undefined : displayLabel}
      style={style}
      className={`group cursor-pointer px-2.5 py-1 text-[11px] font-semibold leading-tight shadow-2xs transition-all ${
        cobertura ? "rounded-[10px]" : "rounded-full"
      } ${className}`}
    >
      {cobertura && (
        <span
          className={`mb-0.5 inline-block rounded-full px-1.5 py-px text-[9.5px] font-bold leading-tight ${
            verPor === "efectivo"
              ? "bg-brand-orange/90 text-white"
              : "bg-muted text-muted-foreground"
          }`}
        >
          {coberturaBadgeText(cobertura, verPor)}
        </span>
      )}
      <div className="truncate">{displayLabel}</div>
    </div>
  );

  if (!cobertura) return pill;
  return (
    <Tooltip content={<CoberturaEventoTooltip cobertura={cobertura} />} delay={200}>
      {pill}
    </Tooltip>
  );
}

export function CalendarioMonthGrid({ gridDays, eventsByDayMap, onSelectEvent, verPor }: Props) {
  return (
    <div className="flex flex-col border border-border rounded-xl bg-card shadow-sm overflow-hidden">
      {/* Weekday Labels Header Row */}
      <div className="grid grid-cols-7 border-b border-border bg-muted/40 text-center text-[11px] font-bold text-muted-foreground uppercase py-2.5">
        {WEEKDAYS.map((day) => (
          <div key={day} className="tracking-wider">
            {day}
          </div>
        ))}
      </div>

      {/* Month Calendar Days Grid (7 columns x 5-6 rows) */}
      <div className="grid grid-cols-7 divide-x divide-y divide-border bg-border/20">
        {gridDays.map((cell, index) => {
          const dayEvents = eventsByDayMap.get(cell.dateStr) || [];

          return (
            <div
              key={`${cell.dateStr}-${index}`}
              className={`flex flex-col min-h-[120px] p-1.5 transition-colors ${
                cell.isCurrentMonth
                  ? "bg-card hover:bg-muted/20"
                  : "bg-muted/10 opacity-40 hover:opacity-60"
              }`}
            >
              {/* Cell Header: Day Number */}
              <div className="flex items-center justify-between mb-1.5 px-1">
                <span />
                {cell.isToday ? (
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-orange text-xs font-bold text-white shadow-sm">
                    {cell.dayNum}
                  </span>
                ) : (
                  <span
                    className={`text-xs font-semibold ${
                      cell.isCurrentMonth ? "text-foreground" : "text-muted-foreground"
                    }`}
                  >
                    {cell.dayNum}
                  </span>
                )}
              </div>

              {/* Day Events Pills List */}
              <div className="flex flex-col gap-1 overflow-y-auto max-h-[140px] pr-0.5 scrollbar-thin">
                {dayEvents.map((evt, evtIdx) => (
                  <EventPill
                    key={`${evt.id}-${cell.dateStr}-${evtIdx}`}
                    evt={evt}
                    verPor={verPor}
                    onSelect={() => onSelectEvent(evt)}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
