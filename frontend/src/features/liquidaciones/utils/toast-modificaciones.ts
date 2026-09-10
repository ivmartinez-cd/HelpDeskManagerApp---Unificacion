import { toast } from "sonner";

/** Toast persistente por liquidación con modificaciones del prestador sin ver
 * (ADR-038) — mismo patrón que `toast-atencion.ts` de WATI: se identifica por
 * `id` para poder retirarlo cuando se marcan como vistas. */
export function mostrarToastModificacion(
  id: string,
  numeroLiquidacion: string | null,
  cantidad: number,
  onVerLiquidacion: () => void,
): void {
  const etiqueta = numeroLiquidacion ?? "sin número";
  toast.warning(
    `Liquidación ${etiqueta}: el prestador modificó ${cantidad} valor${cantidad === 1 ? "" : "es"}`,
    {
      id,
      duration: Infinity,
      closeButton: true,
      action: { label: "Ver liquidación", onClick: onVerLiquidacion },
    },
  );
}

export function retirarToastModificacion(id: string): void {
  toast.dismiss(id);
}
