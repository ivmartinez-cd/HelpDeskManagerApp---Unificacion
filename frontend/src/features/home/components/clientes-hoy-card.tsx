"use client";

import { CalendarCheck2, TriangleAlert } from "lucide-react";
import { useState } from "react";
import type { CalendarEvent, Operador } from "@/features/contadores/types/calendario";
import { cleanTitle, textoDesdeSync } from "@/features/contadores/utils/calendario-format";
import { FALLBACK_COLOR, tint } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";

// Umbral para considerar el sync viejo y avisar: el sync es manual y la
// planificación vale lo que valga la última sincronización.
const STALE_SYNC_HORAS = 24;

export function ClientesHoyCard({
  eventos,
  subtitulo,
  operadores,
  lastSyncedAt,
  loading,
  error,
}: {
  eventos: CalendarEvent[];
  subtitulo: string;
  operadores: Operador[];
  lastSyncedAt: string | null;
  loading: boolean;
  error: string | null;
}) {
  // Capturado una vez por montaje: alcanza para decidir la frescura del sync
  // sin llamar Date.now() en cada render (react-hooks/purity).
  const [ahora] = useState(() => Date.now());
  const porId = new Map(operadores.map((op) => [op.id, op]));
  const syncStale =
    !loading &&
    !error &&
    (!lastSyncedAt || ahora - Date.parse(lastSyncedAt) > STALE_SYNC_HORAS * 3_600_000);
  const visitas = eventos.length === 1 ? "1 visita" : `${eventos.length} visitas`;

  return (
    <DashboardCard
      icon={CalendarCheck2}
      title="Clientes de hoy"
      subtitle={loading ? subtitulo : `${subtitulo} · ${visitas}`}
      loading={loading}
      error={error}
    >
      <div className="flex flex-col gap-2 pt-2.5">
        {eventos.length === 0 ? (
          <span className="font-body text-[13px] text-muted-foreground">
            No hay clientes planificados para hoy.
          </span>
        ) : (
          <ul className="flex max-h-[170px] flex-col gap-[7px] overflow-y-auto pr-0.5">
            {eventos.map((evt) => {
              const operador = evt.operador_id ? porId.get(evt.operador_id) : undefined;
              const color = operador?.color ?? FALLBACK_COLOR;
              const nombre = evt.cliente || cleanTitle(evt.title) || "Sin nombre";
              return (
                <li
                  key={evt.id}
                  title={nombre}
                  className="flex flex-col gap-0.5 rounded-[8px] px-3 py-[9px]"
                  style={{ background: tint(color), borderLeft: `3px solid ${color}` }}
                >
                  <span className="truncate font-heading text-[12.5px] font-bold text-foreground">
                    {nombre}
                  </span>
                  {operador && (
                    <span className="truncate font-body text-[12px]" style={{ color }}>
                      {operador.nombre}
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        )}
        <div
          className={`flex items-center gap-1.5 font-body text-[11px] ${
            syncStale ? "text-amber-600" : "text-muted-foreground"
          }`}
        >
          {syncStale && <TriangleAlert className="h-3 w-3 shrink-0" />}
          <span>{textoDesdeSync(lastSyncedAt)}</span>
        </div>
      </div>
    </DashboardCard>
  );
}
