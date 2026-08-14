"use client";

import { CalendarCheck2, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { contadoresApi } from "@/features/contadores/api/contadores-api";
import type { CalendarEvent, Operador } from "@/features/contadores/types/calendario";
import {
  cleanTitle,
  diasDeAtraso,
  formatDateLocal,
  getEventPillClassName,
  getEventPillInlineStyle,
  textoAtraso,
  textoDesdeSync,
} from "@/features/contadores/utils/calendario-format";
import { useSession } from "@/services/session-provider";
import { Spinner } from "@/shared/components/ui/spinner";

// Umbral para considerar el sync viejo y atenuar/avisar. El sync es manual:
// si nadie sincronizó hace rato, el backlog puede mostrar clientes que en
// Gestión ya se cerraron.
const STALE_SYNC_HORAS = 24;

/** Recorte de "clientes de hoy" + pendientes de arrastre para Inicio, a
 * partir del calendario de Contadores. La visibilidad (operador propio +
 * coberturas) y el corte del backlog los resuelve el backend. */
export function TodayClientsCard() {
  const { modules } = useSession();
  // `can()` sólo refleja grants explícitos; un superadmin ve el módulo sin
  // tenerlos (ver ListVisibleModules), así que el gate correcto es el mismo
  // que usa el sidebar para decidir si mostrar "Contadores".
  const canView = modules.some((m) => m.key === "contadores");

  const today = formatDateLocal(new Date());
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [pendientes, setPendientes] = useState<CalendarEvent[]>([]);
  const [operadores, setOperadores] = useState<Operador[]>([]);
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);
  // `loading` arranca en true solo cuando hay que cargar: si canView es false
  // el componente no renderiza nada y no hay estado de carga que gestionar.
  const [loading, setLoading] = useState<boolean>(canView);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!canView) return;
    const hoy = formatDateLocal(new Date());

    Promise.all([
      contadoresApi.getCalendarioEvents({ start: hoy, end: hoy }),
      contadoresApi.getCalendarioPendientes(hoy),
    ])
      .then(([hoyPage, pendPage]) => {
        setEvents(hoyPage.items);
        setPendientes(pendPage.items);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar la planificación de Inicio:", err);
        setError(err instanceof Error ? err.message : "No se pudo cargar la planificación.");
      })
      .finally(() => setLoading(false));

    // Catálogo para resolver a quién pertenece cada cliente (el evento no
    // trae el nombre del operador).
    contadoresApi
      .listCalendarioOperadores()
      .then(setOperadores)
      .catch((err: unknown) => console.error("Error al cargar el catálogo de operadores:", err));

    // Frescura del sync: el backlog vale lo que valga la última sincronización.
    contadoresApi
      .getSyncStatus()
      .then((status) => setLastSyncedAt(status.last_synced_at))
      .catch((err: unknown) => console.error("Error al consultar el estado de sync:", err));
  }, [canView]);

  const operadorNombreById = new Map(operadores.map((op) => [op.id, op.nombre]));

  if (!canView) return null;

  const syncStale =
    !lastSyncedAt || Date.now() - Date.parse(lastSyncedAt) > STALE_SYNC_HORAS * 3_600_000;

  return (
    <div className="flex w-full flex-col gap-3 rounded-[12px] border border-border bg-card p-5">
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
      ) : (
        <>
          {events.length === 0 ? (
            <span className="font-body text-[13px] text-muted-foreground">
              No hay clientes planificados para hoy.
            </span>
          ) : (
            <ul className="flex max-h-96 flex-col gap-1.5 overflow-y-auto">
              {events.map((evt) => {
                const operadorNombre = evt.operador_id
                  ? operadorNombreById.get(evt.operador_id)
                  : null;
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

          {pendientes.length > 0 && (
            <div className="flex flex-col gap-1.5 border-t border-border pt-3">
              <div className="flex items-center justify-between">
                <span className="font-heading text-[13px] font-bold text-foreground">
                  Pendientes de días anteriores
                </span>
                <span className="rounded-full bg-brand-orange/[0.12] px-2 py-0.5 text-[11px] font-semibold text-brand-orange">
                  {pendientes.length}
                </span>
              </div>
              <ul className="flex max-h-72 flex-col gap-1.5 overflow-y-auto">
                {pendientes.map((evt) => {
                  const operadorNombre = evt.operador_id
                    ? operadorNombreById.get(evt.operador_id)
                    : null;
                  const dias = diasDeAtraso(evt.start, today);
                  return (
                    <li
                      key={evt.id}
                      className={`flex flex-col gap-0.5 rounded-[8px] px-2.5 py-1.5 ${getEventPillClassName(evt)}`}
                      style={getEventPillInlineStyle(evt)}
                      title={evt.cliente || cleanTitle(evt.title)}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate font-body text-[13px] font-semibold">
                          {evt.cliente || cleanTitle(evt.title) || "Sin nombre"}
                        </span>
                        <span className="shrink-0 rounded-full bg-black/20 px-1.5 py-0.5 text-[10px] font-medium">
                          {textoAtraso(dias)}
                        </span>
                      </div>
                      {operadorNombre && (
                        <span className="truncate font-body text-[11px] font-normal text-white/80">
                          {operadorNombre}
                        </span>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          <div
            className={`flex items-center gap-1.5 font-body text-[11px] ${
              syncStale ? "text-amber-600" : "text-muted-foreground"
            }`}
          >
            {syncStale && <TriangleAlert className="h-3 w-3 shrink-0" />}
            <span>{textoDesdeSync(lastSyncedAt)}</span>
          </div>
        </>
      )}
    </div>
  );
}
