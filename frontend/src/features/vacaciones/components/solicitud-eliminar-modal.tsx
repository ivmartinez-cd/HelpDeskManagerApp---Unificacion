"use client";

import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { formatFecha } from "../lib/fechas";
import type { Solicitud } from "../types/vacaciones";

export function SolicitudEliminarModal({
  eliminando,
  busy,
  onClose,
  onConfirm,
}: {
  eliminando: Solicitud;
  busy: boolean;
  onClose: () => void;
  onConfirm: () => void;
}) {
  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title="Eliminar solicitud"
      widthPx={440}
    >
      <p className="font-body text-sm text-foreground">
        ¿Eliminar la solicitud de{" "}
        <span className="font-semibold">{eliminando.empleadoNombre}</span> del{" "}
        {formatFecha(eliminando.startDate)} al {formatFecha(eliminando.endDate)}? Esta
        acción no se puede deshacer.
      </p>
      <div className="mt-5 flex justify-end gap-2">
        <BrandButton variant="outline" onClick={onClose}>
          Volver
        </BrandButton>
        <BrandButton
          onClick={onConfirm}
          loading={busy}
          className="bg-destructive hover:bg-destructive/90"
        >
          Eliminar
        </BrandButton>
      </div>
    </BrandModal>
  );
}
