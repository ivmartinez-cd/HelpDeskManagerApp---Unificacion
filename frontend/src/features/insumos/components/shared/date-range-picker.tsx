"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import type { DateRange } from "../../types/common";
import { EMPTY_VALUE, formatPlainDate, todayInArg } from "../../utils/format";

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
 */

const WEEKDAYS = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"];

const PRESET_KEYS = ["hoy", "semana", "mes", "mespasado", "trimestre", "custom"] as const;
export type DateRangePresetKey = (typeof PRESET_KEYS)[number];

const PRESET_LABELS: Record<DateRangePresetKey, string> = {
  hoy: "Hoy",
  semana: "Esta semana",
  mes: "Este mes",
  mespasado: "Mes pasado",
  trimestre: "Último trimestre",
  custom: "Personalizado",
};

/** `YYYY-MM-DD` → `Date` a medianoche LOCAL. Nunca usar `new Date(key)` a
 * secas: eso parsea el string como UTC y corre un día para atrás en -03. */
function parseKey(key: string): Date {
  const [year, month, day] = key.split("-").map(Number);
  return new Date(year, month - 1, day);
}

/** `Date` local → `YYYY-MM-DD`, sin pasar por `toISOString()` (que convierte a
 * UTC y vuelve a correr el día). */
function toKey(date: Date): string {
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

/** Rango de cada preset, calculado sobre el día de hoy en Argentina.
 * `custom` devuelve `null`: solo cambia el modo, no toca las fechas. */
export function rangeForPreset(preset: DateRangePresetKey): DateRange | null {
  const today = parseKey(todayInArg());
  const y = today.getFullYear();
  const m = today.getMonth();
  switch (preset) {
    case "hoy":
      return { startDate: toKey(today), endDate: toKey(today) };
    case "semana": {
      // Semana que arranca el lunes (getDay(): 0 = domingo).
      const offset = (today.getDay() + 6) % 7;
      const monday = new Date(y, m, today.getDate() - offset);
      return { startDate: toKey(monday), endDate: toKey(today) };
    }
    case "mes":
      return { startDate: toKey(new Date(y, m, 1)), endDate: toKey(today) };
    case "mespasado":
      return { startDate: toKey(new Date(y, m - 1, 1)), endDate: toKey(new Date(y, m, 0)) };
    case "trimestre":
      return { startDate: toKey(new Date(y, m - 3, today.getDate())), endDate: toKey(today) };
    default:
      return null;
  }
}

/** Celdas del mes: los huecos iniciales van como `null`. */
function buildMonthCells(year: number, month: number): (Date | null)[] {
  const first = new Date(year, month, 1);
  const leading = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: (Date | null)[] = Array.from({ length: leading }, () => null);
  for (let day = 1; day <= daysInMonth; day++) cells.push(new Date(year, month, day));
  return cells;
}

interface DateRangePickerProps {
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
              "rounded-[8px] px-3 py-2 text-left font-body text-sm transition-colors",
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
              className="rounded-[8px] border border-border px-4 py-2.5 font-body text-[13px] font-semibold text-muted-foreground transition-colors hover:bg-muted"
            >
              Limpiar
            </button>
            <button
              type="button"
              onClick={handleApply}
              className="rounded-[8px] bg-brand-orange px-4 py-2.5 font-body text-[13px] font-bold text-white transition-colors hover:bg-brand-orange-hover"
            >
              Aplicar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function RangeEnd({ label, value }: { label: string; value?: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="font-body text-[11px] font-semibold uppercase tracking-[.04em] text-muted-foreground">
        {label}
      </span>
      <span className="font-heading text-sm font-bold text-foreground">
        {value ? formatPlainDate(value) : EMPTY_VALUE}
      </span>
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

function MonthGrid({
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
            className="rounded-[6px] p-1 text-muted-foreground hover:text-brand-orange"
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
            className="rounded-[6px] p-1 text-muted-foreground hover:text-brand-orange"
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
                disabled && "cursor-not-allowed text-muted-foreground/40",
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
          "flex items-center gap-2 rounded-[8px] border border-border bg-card px-3.5 py-2.5 font-body text-sm transition-colors hover:bg-muted",
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
