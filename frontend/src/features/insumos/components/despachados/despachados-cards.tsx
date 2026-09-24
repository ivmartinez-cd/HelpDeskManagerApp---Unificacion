"use client";

import { Check, MapPin, TriangleAlert, Truck, Undo2, type LucideIcon } from "lucide-react";
import { BrandSkeleton } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import type { ColorSemaforo, ResumenDespachos } from "../../types/despachados";
import { TONO, textoLimite } from "./semaforo";

/** Las 5 tarjetas-filtro (patrón KpiTile del handoff). Cada una es un
 * `button` con `aria-pressed`: tocarla filtra la tabla por su color (y la
 * vuelve a tocar para sacar el filtro); el `<select>` de color de la tabla y
 * las tarjetas comparten el mismo estado. */

export interface TarjetaDef {
  /** Valor del filtro `colores` que aplica (igual al del `<select>`). */
  clave: string;
  label: string;
  tono: ColorSemaforo;
  icon: LucideIcon;
}

export const TARJETAS: TarjetaDef[] = [
  { clave: "naranja", label: "Visita fallida", tono: "naranja", icon: TriangleAlert },
  { clave: "rojo", label: "En sucursal", tono: "rojo", icon: MapPin },
  { clave: "verde,amarillo", label: "En tránsito", tono: "verde", icon: Truck },
  { clave: "gris", label: "Devueltos (30 días)", tono: "gris", icon: Undo2 },
  { clave: "cerrado", label: "Entregados (30 días)", tono: "cerrado", icon: Check },
];

function cantidad(resumen: ResumenDespachos, clave: string): number {
  return clave
    .split(",")
    .reduce((suma, color) => suma + (resumen.porColor[color as ColorSemaforo] ?? 0), 0);
}

function pista(resumen: ResumenDespachos, clave: string): string {
  if (clave === "naranja") {
    const n = resumen.naranjasSinAccion;
    return n ? `${n} sin acción registrada` : "Todas con acción registrada";
  }
  if (clave === "rojo") {
    const texto = textoLimite(resumen.limiteMasProximo, resumen.diasHabilesLimiteMasProximo);
    return texto ? `La más próxima ${texto}` : "Ninguno esperando retiro";
  }
  if (clave === "verde,amarillo") return `${resumen.porColor.amarillo ?? 0} sin movimiento (amarillo)`;
  return "Últimos 30 días";
}

interface Props {
  resumen: ResumenDespachos | null;
  seleccion: string;
  onSeleccion: (clave: string) => void;
}

export function DespachadosCards({ resumen, seleccion, onSeleccion }: Props) {
  return (
    <section
      aria-label="Resumen. Tocá una tarjeta para filtrar la tabla."
      className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-5"
    >
      {TARJETAS.map((t) => {
        const pressed = seleccion === t.clave;
        const Icon = t.icon;
        const tono = TONO[t.tono];
        return (
          <button
            key={t.clave}
            type="button"
            aria-pressed={pressed}
            onClick={() => onSeleccion(pressed ? "" : t.clave)}
            className={cn(
              "flex cursor-pointer flex-col gap-1.5 rounded-[12px] border border-border bg-card px-[18px] py-4 text-left transition-[border-color,box-shadow] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-orange",
              pressed ? tono.cardPressed : tono.cardHover,
            )}
          >
            <span className="flex items-center justify-between gap-2">
              <span className="inline-flex items-center gap-1.5 font-body text-[11px] font-bold uppercase leading-[1.4] tracking-[.05em] text-muted-foreground">
                <Icon className={cn("h-3.5 w-3.5", tono.text)} aria-hidden="true" />
                {t.label}
              </span>
              <span
                className={cn(
                  "font-body text-[10px] font-bold uppercase leading-none tracking-[.05em]",
                  tono.text,
                  !pressed && "invisible",
                )}
              >
                Filtrando
              </span>
            </span>
            {resumen ? (
              <>
                <span className={cn("font-heading text-[26px] font-extrabold leading-[1.15] tabular-nums", tono.text)}>
                  {cantidad(resumen, t.clave).toLocaleString("es-AR")}
                </span>
                <span className="min-h-4 font-body text-xs leading-4 text-muted-foreground">
                  {pista(resumen, t.clave)}
                </span>
              </>
            ) : (
              <>
                <BrandSkeleton className="h-[30px] w-16" />
                <BrandSkeleton className="h-4 w-32" />
              </>
            )}
          </button>
        );
      })}
    </section>
  );
}
