import type { ReactNode } from "react";
import { cn } from "@/shared/utils/cn";

/** Pill de estado del Patrón 1 del handoff (`border-radius: 20px`, tinte del
 * color + texto en el color pleno).
 *
 * El handoff define 3 tonos (Activo naranja / Atención rojo / OK verde). Se
 * agregó un cuarto (`advertencia`, amarillo) porque los estados reales del
 * backend son CUATRO — `statusKey` de `RequestRowOut` puede ser `critical`,
 * `urgent`, `warning` o `good` — y aplastar `urgent` y `warning` en el mismo
 * naranja perdía información que la app vieja sí mostraba. Es el semáforo
 * rojo-amarillo-verde estándar del proyecto, no un color de marca nuevo.
 * `neutral` es el fallback para estados que no son de severidad (p.ej. los
 * `supplyStatus` de Canal Directo).
 *
 * Los colores del handoff son los valores de tema claro; cada tono tiene su
 * variante `dark:` más luminosa porque estas pills viven en tablas del shell,
 * que sí responde al toggle de tema (a diferencia de `BrandModal` y compañía).
 */
export type StatusTone = "activo" | "atencion" | "advertencia" | "ok" | "neutral";

const toneClasses: Record<StatusTone, string> = {
  activo: "bg-[rgba(247,148,29,.12)] text-[#F7941D]",
  atencion: "bg-[rgba(239,68,68,.1)] text-[#dc2626] dark:text-[#f87171]",
  advertencia: "bg-[rgba(234,179,8,.12)] text-[#a16207] dark:text-[#facc15]",
  ok: "bg-[rgba(34,197,94,.1)] text-[#16a34a] dark:text-[#4ade80]",
  neutral: "bg-[rgba(88,89,91,.12)] text-[#58595B] dark:text-[#b5b5b5]",
};

/** Mapea el `statusKey` que devuelve el backend al tono correspondiente.
 * Cualquier clave desconocida cae en `neutral` en vez de romper. */
export function toneForStatusKey(statusKey: string | null | undefined): StatusTone {
  switch (statusKey) {
    case "critical":
      return "atencion";
    case "urgent":
      return "activo";
    case "warning":
      return "advertencia";
    case "good":
      return "ok";
    default:
      return "neutral";
  }
}

interface StatusBadgeProps {
  tone?: StatusTone;
  children: ReactNode;
  className?: string;
}

export function StatusBadge({ tone = "neutral", children, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center whitespace-nowrap rounded-[20px] px-2.5 py-1 font-body text-[11px] font-bold leading-none",
        toneClasses[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
