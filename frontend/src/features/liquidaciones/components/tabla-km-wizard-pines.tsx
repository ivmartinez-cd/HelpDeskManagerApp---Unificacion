"use client";

import type { EstadoAsistenteKm } from "../types/liquidaciones";
import { SeccionTier0 } from "./tabla-km-wizard-pines-tier0";
import { SeccionTier1, SeccionTier1b } from "./tabla-km-wizard-pines-tier1";
import { SeccionWorklistFinal } from "./tabla-km-wizard-pines-worklist";

/** Paso Pines. El listado es cache-first (sin Google); la verificación con
 * Google solo corre tras confirmar el costo. Corregir no consulta nada. */
export function PasoPines({ prestadorId, estado, onCambio }: {
  prestadorId: string; estado: EstadoAsistenteKm; onCambio: () => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <SeccionTier0 prestadorId={prestadorId} />
      <SeccionTier1 prestadorId={prestadorId} />
      <SeccionTier1b prestadorId={prestadorId} />
      <SeccionWorklistFinal
        prestadorId={prestadorId}
        tope={estado.topePorCorrida}
        estimacionAuditarPines={estado.estimacionAuditarPines}
        onCambio={onCambio}
      />
    </div>
  );
}
