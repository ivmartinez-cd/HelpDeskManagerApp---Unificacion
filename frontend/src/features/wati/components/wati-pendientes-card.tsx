"use client";

import { MessageCircle } from "lucide-react";
import Link from "next/link";
import { DashboardCard } from "@/features/home/components/dashboard-card";
import {
  CardEmpty,
  CardLink,
  CountBadge,
  Freshness,
} from "@/features/home/components/dashboard-card-bits";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import type { ConversacionPendiente, WatiPendientesResumen } from "../types/wati";
import { COLOR_NIVEL, SYNC_VENCIDA_MIN, nivelEspera, textoEspera } from "../utils/espera";
import { MisChatsWatiBanner } from "./mis-chats-wati-banner";

function FilaPendiente({ p }: { p: ConversacionPendiente }) {
  const color = COLOR_NIVEL[nivelEspera(p.minutos_esperando)];
  return (
    <li className="flex items-center gap-2 rounded-[6px] px-1.5 py-1">
      <span
        className="inline-block h-2 w-2 shrink-0 rounded-full"
        style={{ backgroundColor: color }}
        aria-hidden="true"
      />
      <span className="min-w-0 flex-1 leading-tight">
        <span className="block truncate font-body text-[12.5px] font-semibold text-foreground">
          {p.nombre}
        </span>
        <span
          className={cn(
            "block truncate font-body text-[11px]",
            p.sin_asignar ? "font-bold text-brand-orange" : "text-muted-foreground",
          )}
        >
          {p.sin_asignar ? "Sin asignar" : p.operador_nombre}
        </span>
      </span>
      <span
        className="shrink-0 font-heading text-[11.5px] font-extrabold tabular-nums"
        style={{ color }}
      >
        {textoEspera(p.minutos_esperando)}
      </span>
    </li>
  );
}

/** Card de Inicio: chats de WhatsApp (WATI) en los que el cliente escribió y
 * ningún operador humano respondió todavía, del más viejo al más nuevo.
 * Semáforo por minutos de espera; "Sin asignar" resaltado porque es el caso
 * típico de "nadie lo vio". Es la única card con botón primario, y solo
 * cuando hay chats esperando: es la acción que sí hay que hacer ahora. */
export function WatiPendientesCard({
  resumen,
  pendientes,
  loading,
  error,
}: {
  resumen: WatiPendientesResumen | null;
  pendientes: ConversacionPendiente[];
  loading: boolean;
  error: string | null;
}) {
  const total = resumen?.total ?? 0;
  const nivelMax = nivelEspera(resumen?.max_minutos_esperando ?? 0);

  return (
    <DashboardCard
      icon={MessageCircle}
      title="WhatsApp sin responder"
      subtitle="Chats de clientes esperando respuesta"
      headerRight={
        resumen && total > 0 ? (
          <CountBadge value={total} tone={nivelMax === "critico" ? "bad" : nivelMax === "atencion" ? "warn" : "ok"} />
        ) : undefined
      }
      loading={loading}
      error={error}
      footer={
        resumen ? (
          <>
            <Freshness at={resumen.sincronizado_at} staleAfterMin={SYNC_VENCIDA_MIN} prefix="Sincronizado" />
            <span className="flex items-center gap-3">
              {resumen.inbox_url && (
                <CardLink href={resumen.inbox_url} external>
                  Abrir WATI ↗
                </CardLink>
              )}
              {total > 0 ? (
                <Link href="/wati" className={brandButtonClasses({ size: "sm" })}>
                  Responder →
                </Link>
              ) : (
                <CardLink href="/wati">Ver detalle →</CardLink>
              )}
            </span>
          </>
        ) : undefined
      }
    >
      {!resumen ? (
        <CardEmpty>Sin datos disponibles.</CardEmpty>
      ) : (
        <>
          <MisChatsWatiBanner />
          {total === 0 ? (
            <CardEmpty>Sin chats esperando respuesta.</CardEmpty>
          ) : (
            <ul className="flex flex-col gap-0.5">
              {pendientes.map((p) => (
                <FilaPendiente key={p.wa_id} p={p} />
              ))}
            </ul>
          )}
        </>
      )}
    </DashboardCard>
  );
}
