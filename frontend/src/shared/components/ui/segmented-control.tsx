"use client";

import { useRef } from "react";
import { cn } from "@/shared/utils/cn";

/** Grupo de opciones mutuamente excluyentes estilo "pill" (rol radiogroup),
 * con los tokens dark-aware del design system de marca. Flechas ←→ navegan
 * dentro del grupo; Tab sale del grupo completo (roving tabindex). */

interface SegmentedControlProps {
  options: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
  size?: "sm" | "md";
  label?: string;
}

export function SegmentedControl({
  options,
  value,
  onChange,
  size = "md",
  label,
}: SegmentedControlProps) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  const moveFocus = (from: number, delta: number) => {
    const next = (from + delta + options.length) % options.length;
    refs.current[next]?.focus();
    onChange(options[next].value);
  };

  return (
    <div
      role="radiogroup"
      aria-label={label}
      className="inline-flex w-fit items-center gap-0.5 rounded-[10px] border border-border bg-muted p-0.5"
    >
      {options.map((option, i) => {
        const checked = option.value === value;
        return (
          <button
            key={option.value}
            ref={(el) => {
              refs.current[i] = el;
            }}
            type="button"
            role="radio"
            aria-checked={checked}
            tabIndex={checked ? 0 : -1}
            onClick={() => onChange(option.value)}
            onKeyDown={(e) => {
              if (e.key === "ArrowRight" || e.key === "ArrowDown") {
                e.preventDefault();
                moveFocus(i, 1);
              } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
                e.preventDefault();
                moveFocus(i, -1);
              }
            }}
            className={cn(
              "rounded-[8px] font-body font-semibold outline-none transition-colors focus-visible:ring-2 focus-visible:ring-brand-orange/40",
              size === "sm" ? "px-2.5 py-1 text-xs" : "px-3.5 py-1.5 text-sm",
              checked
                ? "bg-card text-brand-orange shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
