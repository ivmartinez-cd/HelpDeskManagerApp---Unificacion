"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

/** Modal de carga compartido para las pantallas que consultan Siges en vivo
 * con caché fría (equipos sin real, anexos sin facturar, preventivos).
 * "Inteligente" en dos sentidos: espera `aparicionMs` antes de mostrarse
 * (con caché tibia la respuesta llega antes y no flashea — medido ~900 ms
 * con Playwright en equipos-sin-real), y va cambiando el mensaje según el
 * tiempo transcurrido para que la espera no parezca un cuelgue. */

export interface EtapaCarga {
  /** El mensaje aplica mientras los segundos transcurridos sean < `hasta`.
   * La última etapa puede omitirlo (queda abierta). */
  hasta?: number;
  texto: string;
}

interface SigesLoadingModalProps {
  etapas: EtapaCarga[];
  /** Explicación fija abajo del mensaje (qué tarda y cuánto dura la caché). */
  nota: string;
  titulo?: string;
  aparicionMs?: number;
}

function etapaPorSegundos(segundos: number, etapas: EtapaCarga[]): string {
  for (const etapa of etapas) {
    if (etapa.hasta === undefined || segundos < etapa.hasta) return etapa.texto;
  }
  return etapas[etapas.length - 1]?.texto ?? "Consultando…";
}

export function SigesLoadingModal({
  etapas,
  nota,
  titulo = "Consultando Siges",
  aparicionMs = 1000,
}: SigesLoadingModalProps) {
  const [visible, setVisible] = useState(false);
  const [segundos, setSegundos] = useState(0);

  useEffect(() => {
    const aparicion = setTimeout(() => setVisible(true), aparicionMs);
    const reloj = setInterval(() => setSegundos((s) => s + 1), 1000);
    return () => {
      clearTimeout(aparicion);
      clearInterval(reloj);
    };
  }, [aparicionMs]);

  if (!visible) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={titulo}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-[2px]"
    >
      <div className="flex w-[440px] max-w-[calc(100vw-2rem)] flex-col items-center gap-3 rounded-[16px] border border-border bg-card px-8 py-9 text-center shadow-2xl">
        <Loader2 className="h-9 w-9 animate-spin text-brand-orange" aria-hidden="true" />
        <h2 className="font-heading text-lg font-extrabold uppercase tracking-[-.02em] text-foreground">
          {titulo}
        </h2>
        <p aria-live="polite" className="font-body text-sm text-foreground">
          {etapaPorSegundos(segundos, etapas)}
        </p>
        <p className="font-body text-xs leading-relaxed text-muted-foreground">{nota}</p>
        {segundos > 0 && (
          <p className="font-body text-xs tabular-nums text-muted-foreground/70">
            {segundos} s
          </p>
        )}
      </div>
    </div>
  );
}
