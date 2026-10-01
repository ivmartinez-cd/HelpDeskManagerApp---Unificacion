"use client";

import { usePrestadorHistorial } from "../hooks/use-prestador-historial";
import { BrandSkeleton } from "@/shared/components/ui/brand-form";

function formatFecha(iso: string): string {
  // `desde`/`hasta` son fechas puras (sin hora): forzar timeZone: "UTC" evita
  // que se corran un día para atrás en un huso horario negativo (Argentina),
  // porque `new Date("2026-08-12")` parsea a medianoche UTC.
  return new Date(iso).toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "UTC",
  });
}

/** Historial de reasignación de operador de un PST — se carga a demanda
 * cuando se abre el detalle, no en el listado agrupado (no hace falta ahí). */
export function PrestadorHistorialPanel({ prestadorId }: { prestadorId: string }) {
  const historial = usePrestadorHistorial(prestadorId);

  if (historial === null) {
    return (
      <div className="flex flex-col gap-1.5">
        <BrandSkeleton className="h-4 w-full" />
        <BrandSkeleton className="h-4 w-3/4" />
      </div>
    );
  }

  if (historial.length === 0) {
    return <p className="font-body text-xs text-muted-foreground">Sin historial todavía.</p>;
  }

  return (
    <ul className="flex flex-col gap-1.5">
      {historial.map((tramo) => (
        <li key={tramo.id} className="font-body text-xs text-muted-foreground">
          <span className="font-semibold text-foreground">
            {tramo.operadorNombre ?? "Sin asignar"}
          </span>{" "}
          — {formatFecha(tramo.desde)} {tramo.hasta ? `a ${formatFecha(tramo.hasta)}` : "(vigente)"}
        </li>
      ))}
    </ul>
  );
}
