"use client";

import type { FilaCoberturas } from "../types/coberturas";
import { nombreOperadorA, nombreOperadorB } from "../lib/intercambios";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";

interface CancelarCoberturaModalProps {
  fila: FilaCoberturas;
  /** unidad del alcance, para el copy ("franjas", "clientes", "PST") */
  alcanceUnidad: string;
  busy: boolean;
  onVolver: () => void;
  onConfirmar: () => void;
}

/** Confirmación de cancelación. Una cobertura común libera su alcance; un
 * intercambio (ADR-026) cancela las dos mitades a la vez -- nunca queda media
 * permuta vigente. En ambos casos la regla queda registrada, no se borra. */
export function CancelarCoberturaModal({
  fila,
  alcanceUnidad,
  busy,
  onVolver,
  onConfirmar,
}: CancelarCoberturaModalProps) {
  const esIntercambio = fila.tipo === "intercambio";
  const title = esIntercambio ? "Cancelar intercambio" : "Cancelar cobertura";
  return (
    <BrandModal isOpen onClose={onVolver} title={title} widthPx={440}>
      <p className="font-body text-sm text-foreground">
        {fila.tipo === "cobertura" ? (
          <>
            ¿Cancelar la cobertura de{" "}
            <span className="font-semibold">
              {fila.cobertura.ausenteNombre ?? fila.cobertura.ausenteId}
            </span>
            ? Sus {alcanceUnidad} vuelven al operador original de inmediato. La regla queda
            registrada como cancelada, no se borra.
          </>
        ) : (
          <>
            ¿Cancelar el intercambio entre{" "}
            <span className="font-semibold">{nombreOperadorA(fila.intercambio)}</span> y{" "}
            <span className="font-semibold">{nombreOperadorB(fila.intercambio)}</span>? Cada uno
            vuelve a sus {alcanceUnidad} de inmediato. Las dos coberturas del par quedan
            registradas como canceladas, no se borran.
          </>
        )}
      </p>
      <div className="mt-5 flex justify-end gap-2">
        <BrandButton variant="outline" onClick={onVolver}>
          Volver
        </BrandButton>
        <BrandButton
          onClick={onConfirmar}
          loading={busy}
          className="bg-destructive hover:bg-destructive/90"
        >
          {title}
        </BrandButton>
      </div>
    </BrandModal>
  );
}
