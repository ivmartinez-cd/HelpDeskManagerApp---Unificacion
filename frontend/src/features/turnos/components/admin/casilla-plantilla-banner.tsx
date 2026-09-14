"use client";

import { CalendarClock, Info } from "lucide-react";
import { Button } from "@/shared/components/ui/button";

interface CasillaPlantillaBannerProps {
  puedeEditar: boolean;
  onAjustarTurnosHoy: () => void;
}

export function CasillaPlantillaBanner({
  puedeEditar,
  onAjustarTurnosHoy,
}: CasillaPlantillaBannerProps) {
  return (
    <div className="flex items-start gap-3 rounded-[10px] border border-brand-orange/30 bg-brand-orange/5 p-4">
      <Info className="mt-0.5 h-4 w-4 shrink-0 text-brand-orange" />
      <div className="flex flex-1 flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-heading text-xs font-bold text-foreground">
            Plantilla fija semanal permanente
          </p>
          <p className="font-body text-xs text-muted-foreground">
            Los cambios en esta pestaña modifican la grilla base para todos los días a futuro. Para
            cubrir ausencias imprevistas o reacomodar horarios de una fecha puntual sin tocar la
            plantilla base, usá un horario especial.
          </p>
        </div>
        {puedeEditar && (
          <Button
            variant="outline"
            size="sm"
            onClick={onAjustarTurnosHoy}
            className="shrink-0 gap-1.5 border-brand-orange/40 text-brand-orange hover:bg-brand-orange/10"
          >
            <CalendarClock className="h-4 w-4" />
            Ajustar turnos de hoy
          </Button>
        )}
      </div>
    </div>
  );
}
