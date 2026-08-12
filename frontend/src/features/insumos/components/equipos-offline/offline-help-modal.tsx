"use client";

import { BrandModal } from "@/shared/components/ui/brand-modal";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { StatusBadge } from "../shared";

interface OfflineHelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

/** Explica cómo funciona la detección/verificación/baja de Equipos Offline —
 * portado de `OfflineHelpModal.vue` del legacy. El número de equipos por
 * lote de "Verificación puntual" (10) y el label del botón ("Verificar")
 * están ajustados a los valores reales de este puerto, no a los del legacy
 * (que decía "hasta 30" y "Verificar ubicación"). */
export function OfflineHelpModal({ isOpen, onClose }: OfflineHelpModalProps) {
  return (
    <BrandModal isOpen={isOpen} onClose={onClose} title="¿Cómo funciona Equipos Offline?" widthPx={560}>
      <p className="-mt-1 mb-5 font-body text-sm text-muted-foreground">
        Guía de verificación y gestión de bajas de equipos
      </p>

      <div className="flex flex-col gap-6">
        <section className="flex flex-col gap-3">
          <div className="flex items-center gap-2.5">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-orange font-body text-[11px] font-bold text-white">
              1
            </span>
            <h3 className="font-heading text-sm font-bold text-foreground">
              Detección y Criterios de Baja
            </h3>
          </div>
          <ul className="flex flex-col gap-2.5 pl-[30px] font-body text-sm text-muted-foreground">
            <li>
              <strong className="text-foreground">Equipos Offline (+72 hs):</strong> aparecen
              automáticamente en esta pantalla cuando dejan de reportar a SDS.
            </li>
            <li>
              <strong className="text-foreground">Verificación contra Canal Directo:</strong>{" "}
              antes de habilitar la baja, se consulta el estado real en Canal Directo.
            </li>
            <li>
              <StatusBadge tone="atencion" className="mr-1.5 align-middle">
                En bodega
              </StatusBadge>
              <strong className="text-foreground">Candidatos a baja:</strong> equipos confirmados
              sin asignar. Son los únicos que se pueden eliminar de SDS.
            </li>
            <li>
              <StatusBadge tone="advertencia" className="mr-1.5 align-middle">
                En otro cliente
              </StatusBadge>
              <strong className="text-foreground">Informativo:</strong> puede haber discrepancias
              de nombre por formato; se recomienda revisar a mano antes de decidir.
            </li>
          </ul>
        </section>

        <section className="flex flex-col gap-3">
          <div className="flex items-center gap-2.5">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-orange font-body text-[11px] font-bold text-white">
              2
            </span>
            <h3 className="font-heading text-sm font-bold text-foreground">
              Verificación Automática vs. Manual
            </h3>
          </div>
          <ul className="flex flex-col gap-2.5 pl-[30px] font-body text-sm text-muted-foreground">
            <li>
              <strong className="text-foreground">Corrida nocturna:</strong> todas las madrugadas
              se auditan automáticamente los equipos sin verificar.
            </li>
            <li>
              <strong className="text-foreground">Re-chequeo cada 7 días:</strong> los equipos que
              persisten sin cambios se re-verifican semanalmente para cuidar la velocidad del
              servicio SOAP.
            </li>
            <li>
              <strong className="text-foreground">Verificación puntual:</strong> usá el botón
              «Verificar» para auditar inmediatamente un lote de hasta 10 equipos.
            </li>
          </ul>
        </section>
      </div>

      <div className="mt-6 flex justify-end">
        <button type="button" onClick={onClose} className={brandButtonClasses({ className: "px-6" })}>
          Entendido
        </button>
      </div>
    </BrandModal>
  );
}
