"use client";

/** Reemplazo de `<input type="time">`: Chromium fija el reloj de 12/24h
 * según el idioma de la UI del navegador (no el `lang` de la página ni el
 * del sistema) y en 12h corta la hora al rango 1-12 (tipear "17" quedaba
 * en "5"). Acá es un solo campo de texto enmascarado — "HH:MM" armado a
 * partir de hasta 4 dígitos tipeados — sin segmentos separados ni salto de
 * foco entre hora y minutos, para no depender de en qué posición quedó el
 * cursor tras reemplazar una selección.
 * https://issues.chromium.org/issues/40877286 */

import { useEffect, useRef, useState } from "react";
import { Clock } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import {
  aHhmm,
  completarAlDesenfocar,
  digitosDeRaw,
  digitosDeValor,
  formatearDigitos,
} from "@/shared/utils/time-hhmm";

interface TimeInputProps {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  "aria-label"?: string;
}

export function TimeInput({
  value,
  onChange,
  label,
  hint,
  error,
  required,
  disabled,
  className,
  "aria-label": ariaLabel,
}: TimeInputProps) {
  const [digitos, setDigitos] = useState(() => digitosDeValor(value));
  const enFoco = useRef(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!enFoco.current) setDigitos(digitosDeValor(value));
  }, [value]);

  function handleChange(raw: string) {
    const siguiente = digitosDeRaw(raw);
    setDigitos(siguiente);
    if (siguiente.length === 4) onChange(aHhmm(siguiente));
  }

  function handleBlur() {
    enFoco.current = false;
    const completos = completarAlDesenfocar(digitos);
    setDigitos(completos);
    onChange(aHhmm(completos));
  }

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label
          onClick={() => inputRef.current?.focus()}
          className="w-fit cursor-text font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground"
        >
          {label}
        </label>
      )}
      <div
        className={cn(
          "flex w-fit items-center gap-1.5 rounded-[8px] border border-border bg-card px-2.5 py-[7px] font-mono text-sm text-foreground focus-within:ring-2 focus-within:ring-brand-orange/40",
          error && "border-destructive",
          disabled && "opacity-50",
          className,
        )}
      >
        <input
          ref={inputRef}
          type="text"
          inputMode="numeric"
          maxLength={5}
          disabled={disabled}
          aria-label={ariaLabel ?? label ?? "Hora"}
          placeholder="--:--"
          value={formatearDigitos(digitos)}
          onFocus={(e) => {
            enFoco.current = true;
            e.target.select();
          }}
          onBlur={handleBlur}
          onChange={(e) => handleChange(e.target.value)}
          className="w-[6ch] bg-transparent outline-none placeholder:text-muted-foreground/50"
        />
        <Clock className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden />
      </div>
      {required && (
        <input
          type="text"
          required
          value={value}
          onChange={() => {}}
          tabIndex={-1}
          aria-hidden
          className="sr-only"
        />
      )}
      {hint && !error && <p className="font-body text-xs text-muted-foreground">{hint}</p>}
      {error && <p className="font-body text-xs text-destructive">{error}</p>}
    </div>
  );
}
