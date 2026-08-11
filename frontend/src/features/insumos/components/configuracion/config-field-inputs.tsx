"use client";

import { useId } from "react";
import { cn } from "@/shared/utils/cn";
import type {
  BooleanFieldSpec,
  EmailsFieldSpec,
  NumberFieldSpec,
} from "./config-fields";

/** Campos del Patrón 5: label a la izquierda, hint 12px gris a la derecha,
 * control `radius 8px` con foco naranja. El mensaje de error reemplaza al hint
 * y pinta el borde en rojo. */

const controlBase =
  "w-full rounded-[8px] border bg-card px-3 py-2.5 font-body text-sm text-foreground outline-none transition-colors focus:ring-2 disabled:cursor-not-allowed disabled:opacity-60";

function controlClass(invalid: boolean): string {
  return cn(
    controlBase,
    invalid
      ? "border-[#ef4444] focus:border-[#ef4444] focus:ring-[#ef4444]/25"
      : "border-border focus:border-brand-orange focus:ring-brand-orange/30",
  );
}

interface FieldShellProps {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
}

function FieldShell({ id, label, hint, error, children }: FieldShellProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline justify-between gap-3">
        <label htmlFor={id} className="font-body text-[13px] font-semibold text-foreground">
          {label}
        </label>
        {hint && !error && (
          <span className="font-body text-xs text-muted-foreground">{hint}</span>
        )}
      </div>
      {children}
      {error && (
        <p className="font-body text-xs font-semibold text-[#dc2626] dark:text-[#f87171]">
          {error}
        </p>
      )}
    </div>
  );
}

interface NumberFieldProps {
  spec: NumberFieldSpec;
  value: string;
  error?: string;
  disabled: boolean;
  onChange: (value: string) => void;
}

export function NumberField({ spec, value, error, disabled, onChange }: NumberFieldProps) {
  const id = useId();
  return (
    <FieldShell id={id} label={spec.label} hint={spec.hint} error={error}>
      <div className="relative">
        <input
          id={id}
          type="number"
          inputMode="numeric"
          value={value}
          min={spec.min}
          max={spec.max}
          step={1}
          disabled={disabled}
          onChange={(event) => onChange(event.target.value)}
          aria-invalid={Boolean(error)}
          className={cn(controlClass(Boolean(error)), spec.suffix && "pr-20")}
        />
        {spec.suffix && (
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 font-body text-xs text-muted-foreground">
            {spec.suffix}
          </span>
        )}
      </div>
    </FieldShell>
  );
}

interface BooleanFieldProps {
  spec: BooleanFieldSpec;
  value: boolean;
  disabled: boolean;
  onChange: (value: boolean) => void;
}

export function BooleanField({ spec, value, disabled, onChange }: BooleanFieldProps) {
  const id = useId();
  return (
    <div className="flex items-start gap-3 rounded-[8px] border border-border bg-muted/40 px-3 py-2.5">
      <input
        id={id}
        type="checkbox"
        checked={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
        className="mt-0.5 h-4 w-4 cursor-pointer accent-[#F7941D] disabled:cursor-not-allowed"
      />
      <label htmlFor={id} className="cursor-pointer">
        <span className="block font-body text-[13px] font-semibold text-foreground">
          {spec.label}
        </span>
        {spec.hint && (
          <span className="mt-0.5 block font-body text-xs text-muted-foreground">{spec.hint}</span>
        )}
      </label>
    </div>
  );
}

interface EmailsFieldProps {
  spec: EmailsFieldSpec;
  value: string;
  error?: string;
  disabled: boolean;
  onChange: (value: string) => void;
}

export function EmailsField({ spec, value, error, disabled, onChange }: EmailsFieldProps) {
  const id = useId();
  return (
    <FieldShell id={id} label={spec.label} hint={spec.hint} error={error}>
      <textarea
        id={id}
        rows={4}
        value={value}
        disabled={disabled}
        placeholder={"logistica@ejemplo.com\ndepositos@ejemplo.com"}
        onChange={(event) => onChange(event.target.value)}
        aria-invalid={Boolean(error)}
        className={cn(controlClass(Boolean(error)), "resize-y")}
      />
    </FieldShell>
  );
}
