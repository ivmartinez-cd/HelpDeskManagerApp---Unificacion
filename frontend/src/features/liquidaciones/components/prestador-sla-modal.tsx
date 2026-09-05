"use client";

import { BrandModal } from "@/shared/components/ui/brand-modal";
import { PasoSla } from "./alta-prestador/alta-prestador-wizard-cd-sla";
import type { PrestadorLiquidacion } from "../types/liquidaciones";

/** Completa "afuera del asistente" el paso "Módulo SLA" que se salteó al dar de
 * alta el prestador — a diferencia de Siges/Base/CD (que sí tienen su botón en
 * la fila), este paso no tenía ningún camino de vuelta si se saltea una vez. */
export function PrestadorSlaModal({
  prestador,
  onClose,
  onCreado,
}: {
  prestador: PrestadorLiquidacion;
  onClose: () => void;
  onCreado: () => void;
}) {
  return (
    <BrandModal isOpen onClose={onClose} title={`Alta en módulo SLA — ${prestador.nombreCorto}`} widthPx={480}>
      <PasoSla
        prestador={prestador}
        sigesElegida={
          prestador.sigesEmpresaId != null
            ? {
                sigesEmpresaId: prestador.sigesEmpresaId,
                denComercial: prestador.nombre,
                razonSocial: null,
                cuit: prestador.cuit,
                tipo: "PST",
              }
            : null
        }
        onCreado={() => { onCreado(); onClose(); }}
        onSaltear={onClose}
      />
    </BrandModal>
  );
}
