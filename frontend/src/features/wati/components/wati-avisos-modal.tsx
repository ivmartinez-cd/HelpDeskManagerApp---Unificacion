"use client";

import { MessageCircle } from "lucide-react";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import type { ConversacionPendiente } from "../types/wati";
import { COLOR_NIVEL, nivelEspera, textoEspera } from "../utils/espera";

function FilaAviso({ p }: { p: ConversacionPendiente }) {
  const color = COLOR_NIVEL[nivelEspera(p.minutos_esperando)];
  return (
    <li className="flex items-center gap-2.5 rounded-[8px] border border-border px-3 py-2">
      <span
        className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
        style={{ backgroundColor: color }}
        aria-hidden="true"
      />
      <span className="min-w-0 flex-1 leading-tight">
        <span className="block truncate font-body text-[13px] font-semibold text-foreground">
          {p.nombre}
        </span>
        <span
          className={cn(
            "block truncate font-body text-[11.5px]",
            p.sin_asignar ? "font-bold text-brand-orange" : "text-muted-foreground",
          )}
        >
          {p.sin_asignar ? "Sin asignar — nadie lo tiene" : `Asignado a ${p.operador_nombre ?? "—"}`}
        </span>
      </span>
      <span className="shrink-0 font-heading text-[12px] font-extrabold tabular-nums" style={{ color }}>
        {textoEspera(p.minutos_esperando)}
      </span>
    </li>
  );
}

/** Aviso bloqueante para el operador que cubre la casilla ST ahora (ADR-036):
 * se abre cuando un chat de WhatsApp cruza un umbral de espera y no se
 * cierra con Escape ni clic afuera — solo con "Abrir WATI" o "Ya lo vi",
 * que confirman todos los chats listados. Lo monta el provider (por props,
 * no por contexto, para no importar el provider desde acá), así aparece en
 * cualquier módulo, no solo en Inicio. */
export function WatiAvisosModal({
  avisos,
  confirmar,
  inboxUrl,
}: {
  avisos: ConversacionPendiente[];
  confirmar: () => void;
  inboxUrl: string | null;
}) {
  const abierto = avisos.length > 0;

  const abrirWati = () => {
    if (inboxUrl) window.open(inboxUrl, "_blank", "noopener");
    confirmar();
  };

  return (
    <BrandModal
      isOpen={abierto}
      onClose={confirmar}
      title={avisos.length === 1 ? "1 chat de WhatsApp sin responder" : `${avisos.length} chats de WhatsApp sin responder`}
      dismissible={false}
      widthPx={460}
    >
      <p className="mb-4 flex items-start gap-2 font-body text-[13px] text-muted-foreground">
        <MessageCircle className="mt-0.5 h-4 w-4 shrink-0 text-brand-orange" aria-hidden="true" />
        <span>
          Sos el operador de Servicio Técnico en este turno. Estos clientes escribieron y
          nadie les respondió todavía.
        </span>
      </p>
      <ul className="thin-scrollbar mb-5 flex max-h-[45vh] flex-col gap-1.5 overflow-y-auto">
        {avisos.map((p) => (
          <FilaAviso key={p.wa_id} p={p} />
        ))}
      </ul>
      <div className="flex flex-wrap justify-end gap-2">
        <button type="button" onClick={confirmar} className={brandButtonClasses({ variant: "outline" })}>
          Ya lo vi
        </button>
        {inboxUrl && (
          <button type="button" onClick={abrirWati} className={brandButtonClasses()}>
            Abrir WATI
          </button>
        )}
      </div>
    </BrandModal>
  );
}
