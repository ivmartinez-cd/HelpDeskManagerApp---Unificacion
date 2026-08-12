"use client";

import { CalendarCheck2 } from "lucide-react";
import { useEffect, useState } from "react";
import { contadoresApi } from "@/features/contadores/api/contadores-api";
import type { CalendarEvent, Operador } from "@/features/contadores/types/calendario";
import {
  cleanTitle,
  formatDateLocal,
  getEventPillClassName,
  getEventPillInlineStyle,
} from "@/features/contadores/utils/calendario-format";
import { useSession } from "@/services/session-provider";
import { Spinner } from "@/shared/components/ui/spinner";

/** Recorte de "clientes de hoy" para Inicio, a partir del mismo calendario de
 * Contadores (ver useCalendarioEvents) — acá alcanza con pedir el rango de un
 * solo día, sin el resto del estado del calendario completo (mes, sync,
 * filtro por operador). */
export function TodayClientsCard() {
  const { modules } = useSession();
  // `can()` sólo refleja grants explícitos; un superadmin ve el módulo sin
  // tenerlos (ver ListVisibleModules), así que el gate correcto es el mismo
  // que usa el sidebar para decidir si mostrar "Contadores".
  const canView = modules.some((m) => m.key === "contadores");

  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [operadores, setOperadores] = useState<Operador[]>([]);
  // `loading` arranca en true solo cuando hay que cargar: si canView es false
  // el componente no renderiza nada y no hay estado de carga que gestionar.
  const [loading, setLoading] = useState<boolean>(canView);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!canView) return;
    const today = formatDateLocal(new Date());
    contadoresApi
      .getCalendarioEvents({ start: today, end: today })
      .then((page) => setEvents(page.items))
      .catch((err: unknown) => {
        console.error("Error al cargar los clientes de hoy:", err);
        setError(err instanceof Error ? err.message : "No se pudo cargar la planificación de hoy.");
      })
      .finally(() => setLoading(false));

    // Catálogo completo para poder mostrar a quién pertenece cada cliente
    // (evt.operador_id no trae el nombre resuelto) — un usuario regular ve
    // siempre el mismo operador (el suyo, ver GetCalendarEventsUseCase), pero
    // igual sirve para dejarlo explícito en pantalla.
    contadoresApi
      .listCalendarioOperadores()
      .then(setOperadores)
      .catch((err: unknown) => console.error("Error al cargar el catálogo de operadores:", err));
  }, [canView]);

  const operadorNombreById = new Map(operadores.map((op) => [op.id, op.nombre]));

  if (!canView) return null;

  return (
    <div className="flex w-full max-w-sm flex-col gap-3 rounded-[12px] border border-border bg-card p-5">
      <div className="flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-[9px] bg-brand-orange/[0.12] text-brand-orange">
          <CalendarCheck2 className="h-4 w-4" />
        </span>
        <div className="flex flex-col">
          <h2 className="font-heading text-[14.5px] font-bold text-foreground">Clientes de hoy</h2>
          <span className="font-body text-[12.5px] text-muted-foreground">
            Planificación de Contadores
          </span>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-4">
          <Spinner />
        </div>
      ) : error ? (
        <span className="font-body text-[13px] text-destructive">{error}</span>
      ) : events.length === 0 ? (
        <span className="font-body text-[13px] text-muted-foreground">
          No hay clientes planificados para hoy.
        </span>
      ) : (
        <ul className="flex max-h-64 flex-col gap-1.5 overflow-y-auto">
          {events.map((evt) => {
            const operadorNombre = evt.operador_id ? operadorNombreById.get(evt.operador_id) : null;
            return (
              <li
                key={evt.id}
                className={`flex flex-col gap-0.5 rounded-[8px] px-2.5 py-1.5 ${getEventPillClassName(evt)}`}
                style={getEventPillInlineStyle(evt)}
                title={evt.cliente || cleanTitle(evt.title)}
              >
                <span className="truncate font-body text-[13px] font-semibold">
                  {evt.cliente || cleanTitle(evt.title) || "Sin nombre"}
                </span>
                {operadorNombre && (
                  <span className="truncate font-body text-[11px] font-normal text-white/80">
                    {operadorNombre}
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
