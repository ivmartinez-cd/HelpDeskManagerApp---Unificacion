"use client";

import { MessageCircle } from "lucide-react";
import Link from "next/link";
import { useSession } from "@/services/session-provider";
import { useWatiPendientes } from "../providers/wati-pendientes-provider";
import { COLOR_NIVEL, nivelEspera, textoEspera } from "../utils/espera";

/** Banner personal de Inicio (mismo lugar que "Hoy te toca"): chats de
 * WhatsApp asignados al usuario logueado que esperan respuesta. Cruza el
 * email del operador que informa WATI con el email del login; si no hay
 * ninguno propio, no se renderiza nada — es un aviso personal, el resumen
 * del equipo está en la card. */
export function MisChatsWatiBanner() {
  const { user } = useSession();
  const { habilitado, pendientes } = useWatiPendientes();
  if (!habilitado) return null;

  const email = user.email.trim().toLowerCase();
  const propios = pendientes.filter((p) => (p.operador_email ?? "").trim().toLowerCase() === email);
  if (propios.length === 0) return null;

  const masViejo = propios[0];
  const color = COLOR_NIVEL[nivelEspera(masViejo.minutos_esperando)];

  return (
    <Link
      href="/wati"
      className="flex flex-none flex-wrap items-center gap-2 rounded-[12px] border px-4 py-2.5 transition-colors hover:bg-muted/40"
      style={{ borderColor: `${color}66`, backgroundColor: `${color}14` }}
    >
      <MessageCircle className="h-4 w-4 shrink-0" style={{ color }} aria-hidden="true" />
      <span className="font-body text-[13px] font-semibold text-foreground">
        Tenés {propios.length === 1 ? "1 chat asignado" : `${propios.length} chats asignados`} sin
        responder
      </span>
      <span className="font-body text-[12px] text-muted-foreground">
        · {masViejo.nombre} escribió {textoEspera(masViejo.minutos_esperando)}
      </span>
      <span className="ml-auto font-heading text-[11px] font-bold" style={{ color }}>
        Ver →
      </span>
    </Link>
  );
}
