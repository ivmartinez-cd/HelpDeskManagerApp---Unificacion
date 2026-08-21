"use client";

import { AlertTriangle, MessageCircle } from "lucide-react";
import Link from "next/link";
import { DashboardCard } from "@/features/home/components/dashboard-card";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import type { ConversacionPendiente, WatiPendientesResumen } from "../types/wati";
import {
  COLOR_NIVEL,
  nivelEspera,
  sincronizacionVencida,
  textoEspera,
  textoSincronizado,
} from "../utils/espera";

const MAX_FILAS = 6;

function FilaPendiente({ p }: { p: ConversacionPendiente }) {
  const color = COLOR_NIVEL[nivelEspera(p.minutos_esperando)];
  return (
    <li className="flex items-center gap-2 rounded-[6px] px-2 py-1.5">
      <span
        className="inline-block h-2 w-2 shrink-0 rounded-full"
        style={{ backgroundColor: color }}
        aria-hidden="true"
      />
      <span className="min-w-0 flex-1">
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
        className="shrink-0 font-heading text-[12px] font-extrabold tabular-nums"
        style={{ color }}
      >
        {textoEspera(p.minutos_esperando)}
      </span>
    </li>
  );
}

/** Card de Inicio > Planificación: chats de WhatsApp (WATI) en los que el
 * cliente escribió y ningún operador humano respondió todavía, del más
 * viejo al más nuevo. Semáforo por minutos de espera; "Sin asignar"
 * resaltado porque es el caso típico de "nadie lo vio". Los datos los
 * sincroniza el backend contra WATI (polling); la card solo los relee. */
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
  const vencida = resumen ? sincronizacionVencida(resumen.sincronizado_at) : false;
  const visibles = pendientes.slice(0, MAX_FILAS);
  const ocultos = pendientes.length - visibles.length;

  return (
    <DashboardCard
      icon={MessageCircle}
      title="WhatsApp sin responder"
      subtitle="Chats de clientes esperando respuesta"
      headerRight={
        resumen && total > 0 ? (
          <span
            className="rounded-full px-2 py-0.5 font-heading text-[12px] font-bold"
            style={{
              color: COLOR_NIVEL[nivelMax],
              backgroundColor: `${COLOR_NIVEL[nivelMax]}26`,
            }}
          >
            {total}
          </span>
        ) : undefined
      }
      loading={loading}
      error={error}
    >
      {!resumen ? (
        <p className="pt-3 font-body text-[13px] text-muted-foreground">Sin datos disponibles.</p>
      ) : (
        <>
          {vencida && (
            <p className="mt-2 flex items-center gap-1.5 rounded-[6px] bg-amber-500/10 px-2 py-1.5 font-body text-[11px] text-amber-600 dark:text-amber-400">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              Dato posiblemente desactualizado ({textoSincronizado(resumen.sincronizado_at)}).
            </p>
          )}
          {total === 0 ? (
            <p className="pt-3 font-body text-[13px] text-muted-foreground">
              Sin chats esperando respuesta.
            </p>
          ) : (
            <ul className="mt-2 flex flex-col gap-0.5">
              {visibles.map((p) => (
                <FilaPendiente key={p.wa_id} p={p} />
              ))}
              {ocultos > 0 && (
                <li className="px-2 pt-1 font-body text-[11px] text-muted-foreground">
                  y {ocultos} más…
                </li>
              )}
            </ul>
          )}
          <div className="mt-3 flex items-center gap-2">
            <Link href="/wati" className={cn(brandButtonClasses(), "flex-1")}>
              Ver detalle →
            </Link>
            {resumen.inbox_url && (
              <a
                href={resumen.inbox_url}
                target="_blank"
                rel="noopener noreferrer"
                className={cn(brandButtonClasses({ variant: "outline" }), "flex-1")}
              >
                Abrir WATI ↗
              </a>
            )}
          </div>
          {!vencida && (
            <p className="mt-2 text-right font-body text-[10px] text-muted-foreground">
              {textoSincronizado(resumen.sincronizado_at)}
            </p>
          )}
        </>
      )}
    </DashboardCard>
  );
}
