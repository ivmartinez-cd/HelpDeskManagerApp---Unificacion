"use client";

import { ChevronDown } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { BooleanField, EmailsField, NumberField } from "./config-field-inputs";
import type { ConfigSectionSpec } from "./config-fields";
import type { ConfigFormState } from "./config-form";
import type { ConfigErrors } from "./config-validation";

/** Sección del formulario como acordeón (Patrón 5): header clickeable con
 * fondo tintado y título naranja cuando está abierta, chevron que rota, y el
 * cuerpo separado por una línea sutil. */

interface ConfigSectionCardProps {
  section: ConfigSectionSpec;
  open: boolean;
  onToggle: () => void;
  form: ConfigFormState;
  errors: ConfigErrors;
  errorCount: number;
  disabled: boolean;
  onChange: <K extends keyof ConfigFormState>(key: K, value: ConfigFormState[K]) => void;
}

export function ConfigSectionCard({
  section,
  open,
  onToggle,
  form,
  errors,
  errorCount,
  disabled,
  onChange,
}: ConfigSectionCardProps) {
  return (
    <section
      id={`config-section-${section.id}`}
      className="scroll-mt-6 overflow-hidden rounded-[12px] border border-border bg-card"
    >
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className={cn(
          "flex w-full items-center gap-3 px-5 py-4 text-left transition-colors",
          open ? "bg-brand-orange/5" : "hover:bg-muted/50",
        )}
      >
        <span
          className={cn(
            "flex-1 font-heading text-[15px] font-bold",
            open ? "text-brand-orange" : "text-foreground",
          )}
        >
          {section.title}
        </span>
        {errorCount > 0 && (
          <span className="rounded-[12px] bg-[rgba(239,68,68,.1)] px-2.5 py-0.5 font-body text-[11.5px] font-semibold text-[#dc2626] dark:text-[#f87171]">
            {errorCount} error{errorCount === 1 ? "" : "es"}
          </span>
        )}
        <ChevronDown
          className={cn(
            "h-4 w-4 text-muted-foreground transition-transform",
            open && "rotate-180",
          )}
          aria-hidden="true"
        />
      </button>

      {open && (
        <div className="flex flex-col gap-4 border-t border-border px-5 py-5">
          <p className="font-body text-[13px] leading-relaxed text-muted-foreground">
            {section.description}
          </p>
          {section.fields.map((field) => {
            if (field.kind === "boolean") {
              return (
                <BooleanField
                  key={field.key}
                  spec={field}
                  value={form[field.key]}
                  disabled={disabled}
                  onChange={(value) => onChange(field.key, value)}
                />
              );
            }
            if (field.kind === "emails") {
              return (
                <EmailsField
                  key={field.key}
                  spec={field}
                  value={form.logisticsMailTo}
                  error={errors.logisticsMailTo}
                  disabled={disabled}
                  onChange={(value) => onChange("logisticsMailTo", value)}
                />
              );
            }
            return (
              <NumberField
                key={field.key}
                spec={field}
                value={form[field.key]}
                error={errors[field.key]}
                disabled={disabled}
                onChange={(value) => onChange(field.key, value)}
              />
            );
          })}
        </div>
      )}
    </section>
  );
}
