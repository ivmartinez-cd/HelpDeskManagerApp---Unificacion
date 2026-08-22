"use client";

import { useMemo, useState } from "react";
import { cn } from "@/shared/utils/cn";
import type { DateRange } from "../../types/common";
import { todayInArg } from "../../utils/format";
import { MonthGrid, RangeEnd } from "./date-range-month-grid";
import {
  PRESET_KEYS,
  PRESET_LABELS,
  parseKey,
  rangeForPreset,
  type DateRangePresetKey,
} from "./date-range-utils";

export { rangeForPreset, type DateRangePresetKey } from "./date-range-utils";

/** Selector de rango de fechas del Patrón 4 del handoff: panel de presets a la
 * izquierda + dos meses en paralelo + footer con Desde/Hasta y los botones
 * Limpiar/Aplicar.
 *
 * CONTRATO (importante para las pantallas que lo consumen):
 *  - Es 100% **controlado**: `value` es la fuente de verdad y solo cambia
 *    cuando el usuario aprieta "Aplicar" (`onChange(range)`) o "Limpiar"
 *    (`onChange(null)`). Mientras el panel está abierto se edita un borrador
 *    interno — clickear un preset NO dispara `onChange` solo, hace falta
 *    Aplicar. Así el consumidor no recibe un rango a medio armar (start sin
 *    end) ni una ráfaga de requests mientras el usuario tantea.
 *  - NO sincroniza querystring ni nada global. Cada pantalla decide si el
 *    rango va a la URL.
 *
 * Las fechas se manejan como `YYYY-MM-DD` (el mismo formato que aceptan
 * `startDate`/`endDate` de `/api/insumos/estadisticas`), y "hoy" se resuelve
 * en huso Argentina (`utils/format.todayInArg`), no en el del navegador.
 *
 * Helpers puros en `date-range-utils.ts`, grilla mensual en
 * `date-range-month-grid.tsx`, trigger + popover en `date-range-picker-popover.tsx`.
 */

export interface DateRangePickerProps {
  value: DateRange | null;
  onChange: (range: DateRange | null) => void;
  /** Se llama después de Aplicar/Limpiar — el popover lo usa para cerrarse. */
  onApply?: () => void;
  /** Deshabilita días anteriores (p.ej. `earliestDate` de estadísticas). */
  minDate?: string | null;
  /** Deshabilita días posteriores. Default: hoy (no se piden fechas futuras). */
  maxDate?: string | null;
  className?: string;
}

export function DateRangePicker({
  value,
  onChange,
  onApply,
  minDate,
  maxDate,
  className,
}: DateRangePickerProps) {
  const [draft, setDraft] = useState<DateRange | null>(value);
  const [preset, setPreset] = useState<DateRangePresetKey | null>(null);
  // Mientras se elige el segundo extremo el borrador queda "abierto".
  const [pendingStart, setPendingStart] = useState<string | null>(null);
  const [baseMonth, setBaseMonth] = useState(() => {
    const anchor = value ? parseKey(value.startDate) : parseKey(todayInArg());
    return new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  });

  // Si el consumidor cambia `value` por afuera (reset de filtros, navegación),
  // el borrador tiene que seguirlo o el panel muestra un rango fantasma. Se
  // ajusta durante el render, no en un efecto (misma forma que el resync de
  // `sidebar.tsx`), y se compara por contenido y no por referencia: un padre
  // que reconstruye el objeto en cada render entraría en bucle infinito.
  const valueKey = value ? `${value.startDate}/${value.endDate}` : "";
  const [prevValueKey, setPrevValueKey] = useState(valueKey);
  if (valueKey !== prevValueKey) {
    setPrevValueKey(valueKey);
    setDraft(value);
    setPendingStart(null);
  }

  const maxKey = maxDate === undefined ? todayInArg() : maxDate;
  const months = useMemo(
    () => [
      new Date(baseMonth.getFullYear(), baseMonth.getMonth(), 1),
      new Date(baseMonth.getFullYear(), baseMonth.getMonth() + 1, 1),
    ],
    [baseMonth],
  );

  const isDisabled = (key: string) =>
    Boolean((minDate && key < minDate) || (maxKey && key > maxKey));

  const selectDay = (key: string) => {
    if (isDisabled(key)) return;
    setPreset(null);
    if (pendingStart === null) {
      setPendingStart(key);
      setDraft({ startDate: key, endDate: key });
      return;
    }
    const [startDate, endDate] = key < pendingStart ? [key, pendingStart] : [pendingStart, key];
    setDraft({ startDate, endDate });
    setPendingStart(null);
  };

  const applyPreset = (key: DateRangePresetKey) => {
    setPreset(key);
    setPendingStart(null);
    const range = rangeForPreset(key);
    if (!range) return;
    setDraft(range);
    setBaseMonth(() => {
      const start = parseKey(range.startDate);
      return new Date(start.getFullYear(), start.getMonth(), 1);
    });
  };

  const handleClear = () => {
    setDraft(null);
    setPreset(null);
    setPendingStart(null);
    onChange(null);
    onApply?.();
  };

  const handleApply = () => {
    onChange(draft);
    onApply?.();
  };

  return (
    <div className={cn("flex flex-wrap items-start gap-4", className)}>
      <div className="flex min-w-[200px] flex-col gap-1.5 rounded-[12px] border border-border bg-card p-5">
        <span className="mb-1 font-heading text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
          Presets
        </span>
        {PRESET_KEYS.map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => applyPreset(key)}
            aria-pressed={preset === key}
            className={cn(
              "cursor-pointer rounded-[8px] px-3 py-2 text-left font-body text-sm transition-colors",
              preset === key
                ? "border-l-[3px] border-brand-orange bg-brand-orange/10 font-bold text-brand-orange"
                : "text-foreground hover:bg-brand-orange/[.06]",
            )}
          >
            {PRESET_LABELS[key]}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-5 rounded-[12px] border border-border bg-card p-5">
        <div className="flex flex-wrap gap-8">
          {months.map((month, monthIndex) => (
            <MonthGrid
              key={`${month.getFullYear()}-${month.getMonth()}`}
              month={month}
              draft={draft}
              pendingStart={pendingStart}
              isDisabled={isDisabled}
              onSelect={selectDay}
              onPrev={
                monthIndex === 0
                  ? () => setBaseMonth((b) => new Date(b.getFullYear(), b.getMonth() - 1, 1))
                  : undefined
              }
              onNext={
                monthIndex === 1
                  ? () => setBaseMonth((b) => new Date(b.getFullYear(), b.getMonth() + 1, 1))
                  : undefined
              }
            />
          ))}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-border pt-4">
          <div className="flex gap-5">
            <RangeEnd label="Desde" value={draft?.startDate} />
            <div className="w-px bg-border" />
            <RangeEnd label="Hasta" value={draft?.endDate} />
          </div>
          <div className="flex gap-2.5">
            <button
              type="button"
              onClick={handleClear}
              className="cursor-pointer rounded-[8px] border border-border px-4 py-2.5 font-body text-[13px] font-semibold text-muted-foreground transition-colors hover:bg-muted"
            >
              Limpiar
            </button>
            <button
              type="button"
              onClick={handleApply}
              className="cursor-pointer rounded-[8px] bg-brand-orange px-4 py-2.5 font-body text-[13px] font-bold text-white transition-colors hover:bg-brand-orange-hover"
            >
              Aplicar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
