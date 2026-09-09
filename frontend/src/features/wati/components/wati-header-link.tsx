"use client";

import { MessageCircle } from "lucide-react";
import { useWatiPendientes } from "../providers/wati-pendientes-provider";
import { COLOR_NIVEL, nivelEspera } from "../utils/espera";

/** Ícono fijo en el header, en TODA la app (no solo Inicio) — solo para
 * quien tiene el módulo wati; sin él no se renderiza nada (antes se colaba
 * igual el recordatorio de abajo).
 *
 * Con pendientes, muestra la cantidad de chats de WhatsApp esperando
 * respuesta, con el color del semáforo del más viejo (datos del
 * `WatiPendientesProvider`, un solo poller por pestaña). Sin pendientes, el
 * recordatorio "revisar ahora" es para quien **cubre** la franja de ST en
 * este momento (`soyOperadorSt`, turnos reales de la casilla "ST") — no para
 * cualquier usuario logueado mientras la franja está corriendo
 * (`enHorarioSt`, antes usado acá por error: molestaba a todo el mundo
 * durante el horario, no solo a quien lo cubre). Si el fetch de turnos falla, el
 * ícono simplemente no se destaca. Sin URL configurada no se renderiza nada. */
export function WatiHeaderLink({ url }: { url: string | null }) {
  const { habilitado, resumen, soyOperadorSt } = useWatiPendientes();
  const total = habilitado ? (resumen?.total ?? 0) : 0;
  const recordatorio = habilitado && soyOperadorSt;

  if (!url || !habilitado) return null;

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
      title={recordatorio ? "WATI — revisar ahora" : "WATI"}
      className={
        recordatorio
          ? "flex items-center gap-1.5 rounded-full border border-brand-orange bg-brand-orange/[0.12] px-2.5 py-1 font-heading text-[11px] font-bold text-brand-orange"
          : "flex items-center gap-1.5 rounded-[8px] p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
      }
    >
      <MessageCircle className="h-4 w-4" aria-hidden="true" />
      {recordatorio && <span className="hidden sm:inline">Revisar ahora</span>}
    </a>
  );
}
