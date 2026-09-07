import { toast } from "sonner";
import type { ConversacionPendiente } from "../types/wati";
import { textoEspera } from "./espera";

/** Toast persistente del nivel "atención" (15 min sin respuesta), el aviso
 * liviano previo al modal de la hora (ADR-036). Se identifica por `id` para
 * poder retirarlo cuando el chat pasa a crítico o deja de esperar. */
export function mostrarToastAtencion(
  id: string,
  p: ConversacionPendiente,
  inboxUrl: string | null,
): void {
  toast.warning(`${p.nombre} espera respuesta ${textoEspera(p.minutos_esperando)}`, {
    id,
    description: p.sin_asignar
      ? "Chat sin asignar — nadie lo tiene."
      : `Asignado a ${p.operador_nombre ?? p.operador_email ?? "—"}.`,
    duration: Infinity,
    closeButton: true,
    action: inboxUrl
      ? { label: "Abrir WATI", onClick: () => window.open(inboxUrl, "_blank", "noopener") }
      : undefined,
  });
}

export function retirarToast(id: string): void {
  toast.dismiss(id);
}
