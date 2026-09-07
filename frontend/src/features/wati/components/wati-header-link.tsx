"use client";

import { MessageCircle } from "lucide-react";
import { useWatiPendientes } from "../providers/wati-pendientes-provider";
import { COLOR_NIVEL, nivelEspera } from "../utils/espera";

/** Ícono fijo en el header, en TODA la app (no solo Inicio).
 *
 * Con el módulo wati habilitado muestra la cantidad de chats de WhatsApp
 * esperando respuesta, con el color del semáforo del más viejo (datos del
 * `WatiPendientesProvider`, un solo poller por pestaña). Sin pendientes (o
 * sin módulo) cae al comportamiento anterior: recordatorio de revisar WATI
 * durante el horario de Servicio Técnico, tomado de los turnos reales de la
 * casilla "ST" (los lee el provider, ver `useTurnoSt`). Si el fetch de
 * turnos falla, el ícono simplemente no se destaca. Sin URL configurada no
 * se renderiza nada. */
export function WatiHeaderLink({ url }: { url: string | null }) {
  const { habilitado, resumen, enHorarioSt: enHorario } = useWatiPendientes();
  const total = habilitado ? (resumen?.total ?? 0) : 0;

  if (!url) return null;

  if (total > 0) {
    const color = COLOR_NIVEL[nivelEspera(resumen?.max_minutos_esperando ?? 0)];
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        title={`WATI — ${total} chat${total === 1 ? "" : "s"} esperando respuesta`}
        className="flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-heading text-[11px] font-bold"
        style={{ color, borderColor: color, backgroundColor: `${color}1f` }}
      >
        <MessageCircle className="h-4 w-4" aria-hidden="true" />
        <span className="tabular-nums">{total}</span>
        <span className="hidden sm:inline">sin responder</span>
      </a>
    );
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      title={enHorario ? "WATI — revisar ahora" : "WATI"}
      className={
        enHorario
          ? "flex items-center gap-1.5 rounded-full border border-brand-orange bg-brand-orange/[0.12] px-2.5 py-1 font-heading text-[11px] font-bold text-brand-orange"
          : "flex items-center gap-1.5 rounded-[8px] p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
      }
    >
      <MessageCircle className="h-4 w-4" aria-hidden="true" />
      {enHorario && <span className="hidden sm:inline">Revisar ahora</span>}
    </a>
  );
}
