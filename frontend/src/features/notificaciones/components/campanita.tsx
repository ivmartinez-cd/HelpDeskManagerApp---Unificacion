"use client";

import { Bell } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNotificaciones } from "../providers/notificaciones-provider";
import { PanelNotificaciones } from "./panel-notificaciones";

/** Campanita del header con el número de no leídas. Abre un desplegable que
 * cierra con click afuera o Escape (mismo patrón que
 * `DateRangePickerPopover`). */
export function Campanita() {
  const { total } = useNotificaciones();
  const [abierto, setAbierto] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!abierto) return;
    const afuera = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setAbierto(false);
    };
    const escape = (e: KeyboardEvent) => {
      if (e.key === "Escape") setAbierto(false);
    };
    document.addEventListener("mousedown", afuera);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("mousedown", afuera);
      document.removeEventListener("keydown", escape);
    };
  }, [abierto]);

  const etiqueta = total > 0 ? `Notificaciones: ${total} sin leer` : "Notificaciones";
  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setAbierto((v) => !v)}
        aria-label={etiqueta}
        aria-expanded={abierto}
        title={etiqueta}
        className="relative rounded-[8px] p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
      >
        <Bell className="h-5 w-5" aria-hidden="true" />
        {total > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-destructive px-1 font-heading text-[10px] font-bold tabular-nums text-white">
            {total > 99 ? "99+" : total}
          </span>
        )}
      </button>
      {abierto && (
        <div className="fixed inset-x-2 top-16 z-50 overflow-hidden rounded-[12px] border border-border bg-card shadow-lg sm:absolute sm:inset-x-auto sm:right-0 sm:top-full sm:mt-2 sm:w-[380px]">
          <PanelNotificaciones onCerrar={() => setAbierto(false)} />
        </div>
      )}
    </div>
  );
}
