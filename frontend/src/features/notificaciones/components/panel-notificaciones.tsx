"use client";

import { Spinner } from "@/shared/components/ui/spinner";
import { cn } from "@/shared/utils/cn";
import type { Notificacion } from "../api/notificaciones-api";
import { useHistorial } from "../hooks/use-historial";
import { useNotificaciones } from "../providers/notificaciones-provider";
import { AvisosEscritorio } from "./avisos-escritorio";

const FECHA = new Intl.DateTimeFormat("es-AR", {
  timeZone: "America/Argentina/Buenos_Aires",
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
});

/** Contenido del desplegable de la campanita: historial, "marcar todas" y
 * la preferencia de avisos de escritorio. */
export function PanelNotificaciones({ onCerrar }: { onCerrar: () => void }) {
  const { total, noLeidas, abrir, marcarTodas } = useNotificaciones();
  const { items, hayMas, cargando, error, cargarMas } = useHistorial(noLeidas);

  const alAbrir = (n: Notificacion) => {
    abrir(n);
    if (n.url) onCerrar();
  };

  return (
    <div className="flex max-h-[min(70vh,560px)] flex-col">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <span className="font-heading text-sm font-bold text-foreground">Notificaciones</span>
        {total > 0 && (
          <button
            type="button"
            onClick={() => void marcarTodas().catch((e: unknown) => console.error(e))}
            className="text-xs font-semibold text-accent hover:underline"
          >
            Marcar todas como leídas
          </button>
        )}
      </div>
      <ul className="min-h-0 flex-1 overflow-y-auto">
        {items.map((n) => (
          <li key={n.id}>
            <button
              type="button"
              onClick={() => alAbrir(n)}
              className={cn(
                "flex w-full gap-2.5 border-b border-border px-4 py-3 text-left hover:bg-muted",
                !n.leida && "bg-accent/[0.06]",
              )}
            >
              <span
                aria-hidden="true"
                className={cn("mt-1.5 h-2 w-2 flex-none rounded-full", !n.leida && "bg-accent")}
              />
              <span className="min-w-0 flex-1">
                <span className="block text-[13px] font-semibold text-foreground">{n.titulo}</span>
                <span className="mt-0.5 block text-xs text-muted-foreground">{n.cuerpo}</span>
                <span className="mt-1 block text-[11px] tabular-nums text-muted-foreground">
                  {FECHA.format(new Date(n.creada_en))}
                  {!n.leida && <span className="sr-only"> — no leída</span>}
                </span>
              </span>
            </button>
          </li>
        ))}
        {cargando && items.length === 0 && (
          <li className="flex justify-center py-6">
            <Spinner />
          </li>
        )}
        {!cargando && !error && items.length === 0 && (
          <li className="px-4 py-6 text-center text-sm text-muted-foreground">
            No tenés notificaciones.
          </li>
        )}
        {error && <li className="px-4 py-4 text-center text-sm text-destructive">{error}</li>}
        {hayMas && (
          <li className="flex justify-center py-2">
            <button
              type="button"
              onClick={cargarMas}
              disabled={cargando}
              className="text-xs font-semibold text-accent hover:underline disabled:opacity-50"
            >
              Ver más
            </button>
          </li>
        )}
      </ul>
      <AvisosEscritorio />
    </div>
  );
}
