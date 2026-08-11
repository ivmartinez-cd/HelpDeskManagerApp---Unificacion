"use client";

import { Check } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import type { ConfigSectionSpec } from "./config-fields";

/** Sidebar sticky de navegación por sección del Patrón 5.
 *
 * Sección activa: borde izquierdo naranja de 3px + fondo tintado + texto en
 * negrita naranja. Sección completada (sin errores de validación): checkmark
 * circular verde a la derecha. Si tiene errores, el checkmark se reemplaza por
 * un punto rojo. */

interface ConfigNavProps {
  sections: readonly ConfigSectionSpec[];
  activeId: string;
  errorCountBySection: Readonly<Record<string, number>>;
  onSelect: (sectionId: string) => void;
}

export function ConfigNav({
  sections,
  activeId,
  errorCountBySection,
  onSelect,
}: ConfigNavProps) {
  return (
    <nav
      aria-label="Secciones de configuración"
      className="sticky top-6 hidden w-[220px] flex-none self-start rounded-[12px] border border-border bg-card py-4 lg:block"
    >
      <div className="mb-3 px-5">
        <p className="font-heading text-[15px] font-extrabold text-foreground">Configuración</p>
        <p className="mt-0.5 font-body text-xs text-muted-foreground">
          {sections.length} secciones
        </p>
      </div>
      <ul className="flex flex-col">
        {sections.map((section) => {
          const active = section.id === activeId;
          const errorCount = errorCountBySection[section.id] ?? 0;
          return (
            <li key={section.id}>
              <button
                type="button"
                onClick={() => onSelect(section.id)}
                aria-current={active ? "true" : undefined}
                className={cn(
                  "flex w-full items-center gap-2 border-l-[3px] px-[17px] py-2.5 text-left font-body text-[13.5px] transition-colors",
                  active
                    ? "border-brand-orange bg-brand-orange/[.06] font-bold text-brand-orange"
                    : "border-transparent text-muted-foreground hover:bg-muted/50",
                )}
              >
                <span className="flex-1">{section.title}</span>
                {errorCount > 0 ? (
                  <span
                    className="h-2 w-2 flex-none rounded-full bg-[#ef4444]"
                    aria-label={`${errorCount} error(es)`}
                  />
                ) : (
                  <span
                    className="flex h-4 w-4 flex-none items-center justify-center rounded-full bg-[#22c55e] text-white"
                    aria-label="Sección completa"
                  >
                    <Check className="h-2.5 w-2.5" strokeWidth={3} aria-hidden="true" />
                  </span>
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
