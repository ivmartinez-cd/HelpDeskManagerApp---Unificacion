"use client";

import { useState } from "react";
import { MisTareasVarias } from "./mis-tareas-varias";
import { SolicitudesTvPendientes } from "./solicitudes-tv-pendientes";
import { monthValueToPeriodo } from "../hooks/use-mis-solicitudes-tv";
import { useSession } from "@/services/session-provider";

function currentMonthValue(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

/** /tareas-varias: una pantalla, dos vistas según permiso — mismo criterio
 * que Vacaciones (Solicitudes propias + cola de aprobación). Quien tiene
 * `approve` ve la cola de pendientes (y puede cargar TV a nombre de otro
 * técnico); quien tiene `create` ve su propio formulario + historial. Un
 * supervisor con las dos suele tener ambas (ver Bono Técnicos para separar
 * "puede cargar Días" de "puede aprobar TV", que ya no son lo mismo acá). */
export function TareasVariasView() {
  const { user, can } = useSession();
  const puedeCrear = user.isSuperadmin || can("tareas-varias", "create");
  const puedeAprobar = user.isSuperadmin || can("tareas-varias", "approve");
  const [monthValue, setMonthValue] = useState(currentMonthValue());

  return (
    <div className="flex flex-col gap-6">
      {puedeAprobar && (
        <div className="flex flex-col gap-4 px-9 pt-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex flex-col gap-1.5">
              <h1 className="font-heading text-[25px] font-extrabold text-foreground">
                Tareas Varias
              </h1>
              <p className="font-body text-sm text-muted-foreground">
                Solicitudes de TV de todos los técnicos, para aprobar o rechazar.
              </p>
            </div>
            <label className="flex flex-col gap-1">
              <span className="font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
                Período
              </span>
              <input
                type="month"
                value={monthValue}
                onChange={(e) => setMonthValue(e.target.value)}
                className="rounded-[8px] border border-border bg-card px-3 py-1.5 font-body text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand-orange/60"
              />
            </label>
          </div>
          <SolicitudesTvPendientes periodo={monthValueToPeriodo(monthValue)} enabled />
        </div>
      )}
      {puedeCrear && <MisTareasVarias />}
    </div>
  );
}
