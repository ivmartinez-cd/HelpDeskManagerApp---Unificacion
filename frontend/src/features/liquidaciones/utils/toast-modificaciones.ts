import { toast } from "sonner";

/** Toast persistente por liquidación con modificaciones del prestador sin ver
 * (ADR-038) — mismo patrón que `toast-atencion.ts` de WATI: se identifica por
 * `id` para poder retirarlo cuando se marcan como vistas. `onDismiss` cubre el
 * cierre con la cruz (X) — sonner lo dispara tanto ahí como en un
 * `toast.dismiss(id)` programático. */
export function mostrarToastModificacion(
  id: string,
  numeroLiquidacion: string | null,
  cantidad: number,
  onVerLiquidacion: () => void,
  onDismiss: () => void,
): void {
  const etiqueta = numeroLiquidacion ?? "sin número";
  toast.warning(
    `Liquidación ${etiqueta}: el prestador modificó ${cantidad} valor${cantidad === 1 ? "" : "es"}`,
    {
      id,
      duration: Infinity,
      closeButton: true,
      action: { label: "Ver liquidación", onClick: onVerLiquidacion },
      onDismiss,
    },
  );
}

export function retirarToastModificacion(id: string): void {
  toast.dismiss(id);
}
