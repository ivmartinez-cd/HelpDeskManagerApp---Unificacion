"use client";

import { Wrench } from "lucide-react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import type { PuntoMapaPreventivo } from "../types/preventivos";

interface CargarPreventivoModalProps {
  punto: PuntoMapaPreventivo;
  onClose: () => void;
}

/** Disparado desde el botón "Cargar preventivo" del popup del mapa. Todavía
 * NO escribe en Gestión/Siges: el ADR-019 §3 dejó la creación real del
 * incidente vía wsAyC explícitamente fuera de alcance (escritura contra
 * producción, requiere su propio plan con dryRun) y persistNewIncident hoy
 * solo sabe crear tipo 101 Correctivo, no 102 Preventivo. Esta es la maqueta
 * de la interacción a falta de definir ese mecanismo — decisión del usuario
 * de avanzar solo con la UI por ahora. */
export function CargarPreventivoModal({ punto, onClose }: CargarPreventivoModalProps) {
  return (
    <BrandModal isOpen title="Cargar preventivo" onClose={onClose} widthPx={420}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-0.5">
          <p className="font-body text-sm font-semibold text-foreground">{punto.cliente}</p>
          <p className="font-body text-xs text-muted-foreground">
            {punto.sucursal} · {punto.zona}
          </p>
          {punto.domicilio && (
            <p className="font-body text-xs text-muted-foreground">{punto.domicilio}</p>
          )}
        </div>

        <div className="flex items-start gap-3 rounded-[8px] bg-muted/30 px-4 py-3">
          <Wrench className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
          <p className="font-body text-xs text-muted-foreground">
            Todavía no está definido cómo registrar el preventivo real en Gestión (ver
            ADR-019). Esta pantalla es la maqueta del flujo — por ahora no escribe nada en
            Siges.
          </p>
        </div>

        <div className="flex justify-end pt-2">
          <BrandButton variant="outline" onClick={onClose}>
            Cerrar
          </BrandButton>
        </div>
      </div>
    </BrandModal>
  );
}
