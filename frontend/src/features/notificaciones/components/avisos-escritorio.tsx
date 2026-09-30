"use client";

import { Switch } from "@/shared/components/ui/switch";
import { useNotificaciones } from "../providers/notificaciones-provider";

const MOTIVO: Partial<Record<string, string>> = {
  unsupported:
    "Este navegador no permite avisos de Windows en esta dirección: solo funcionan por HTTPS o en la PC que corre la app.",
  denied:
    "Bloqueaste las notificaciones para este sitio. Habilitalas desde el candado de la barra de direcciones.",
};

/** Pie del panel: prender los avisos de escritorio (Windows) para las
 * notificaciones nuevas. Preferencia de este navegador, no de la cuenta. */
export function AvisosEscritorio() {
  const { escritorio } = useNotificaciones();
  if (!escritorio.mounted) return null;

  const motivo = MOTIVO[escritorio.support];
  return (
    <div className="flex flex-col gap-1.5 border-t border-border px-4 py-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-semibold text-foreground">
          Avisar también con notificación de Windows
        </span>
        <Switch
          checked={escritorio.enabled}
          onCheckedChange={(v) => void escritorio.setEnabled(v)}
          disabled={Boolean(motivo)}
          label="Avisar también con notificación de Windows"
        />
      </div>
      {motivo && <p className="text-[11px] leading-snug text-muted-foreground">{motivo}</p>}
    </div>
  );
}
