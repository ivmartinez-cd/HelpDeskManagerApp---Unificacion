"use client";

import { CalendarCheck2 } from "lucide-react";
import type { CalendarEvent, Operador } from "@/features/contadores/types/calendario";
import { cleanTitle } from "@/features/contadores/utils/calendario-format";
import { FALLBACK_COLOR, accentText, tint } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";
import { CardEmpty, CardLink, CountBadge, Freshness } from "./dashboard-card-bits";

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
  onRetry,
}: {
  eventos: CalendarEvent[];
  subtitulo: string;
  operadores: Operador[];
  lastSyncedAt: string | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}) {
  const porId = new Map(operadores.map((op) => [op.id, op]));

  return (
    <DashboardCard
      icon={CalendarCheck2}
      title="Clientes de hoy"
      subtitle={subtitulo}
      loading={loading}
      error={error}
      onRetry={onRetry}
      headerRight={eventos.length > 0 ? <CountBadge value={eventos.length} tone="brand" /> : undefined}
      footer={
        <>
          <Freshness at={lastSyncedAt} staleAfterMin={STALE_SYNC_HORAS * 60} prefix="Sincronizado" />
          <CardLink href="/contadores/calendario">Ver calendario →</CardLink>
        </>
      }
    >
      {eventos.length === 0 ? (
        <CardEmpty>No hay clientes planificados para hoy.</CardEmpty>
      ) : (
        <ul className="flex flex-col gap-1.5 pr-0.5">
          {eventos.map((evt) => {
            const operador = evt.operador_id ? porId.get(evt.operador_id) : undefined;
            const color = operador?.color ?? FALLBACK_COLOR;
            const nombre = evt.cliente || cleanTitle(evt.title) || "Sin nombre";
            return (
              <li
                key={evt.id}
                title={nombre}
                className="flex items-center justify-between gap-2 rounded-[8px] px-2.5 py-1.5"
                style={{ background: tint(color), borderLeft: `3px solid ${color}` }}
              >
                <span className="truncate font-heading text-[12.5px] font-bold text-foreground">
                  {nombre}
                </span>
                {operador && (
                  <span
                    className="shrink-0 truncate font-body text-[11.5px] font-semibold"
                    style={{ color: accentText(color) }}
                  >
                    {operador.nombre}
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </DashboardCard>
  );
}
