"use client";

import { AlertTriangle, MessageCircle, RefreshCw } from "lucide-react";
import { useState } from "react";
import { useSession } from "@/services/session-provider";
import { BrandButton, BrandStatTile } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { StatsTable, type StatsColumn } from "@/shared/components/ui/stats-table";
import { watiApi } from "../api/wati-api";
import { useWatiPendientes } from "../providers/wati-pendientes-provider";
import type { ConversacionPendiente } from "../types/wati";
import {
  COLOR_NIVEL,
  nivelEspera,
  sincronizacionVencida,
  textoEspera,
  textoSincronizado,
} from "../utils/espera";

function formatHora(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return `${d.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit" })} ${d.toLocaleTimeString(
    "es-AR",
    { hour: "2-digit", minute: "2-digit" },
  )}`;
}

const columns: StatsColumn<ConversacionPendiente>[] = [
  {
    key: "espera",
    label: "Esperando",
    className: "w-36",
    render: (row) => {
      const color = COLOR_NIVEL[nivelEspera(row.minutos_esperando)];
      return (
        <span className="flex items-center gap-2 font-semibold tabular-nums" style={{ color }}>
          <span
            className="inline-block h-2 w-2 shrink-0 rounded-full"
            style={{ backgroundColor: color }}
            aria-hidden="true"
          />
          {textoEspera(row.minutos_esperando)}
        </span>
      );
    },
  },
  { key: "nombre", label: "Cliente", render: (row) => <span className="font-semibold">{row.nombre}</span> },
  { key: "wa_id", label: "Número", render: (row) => <span className="tabular-nums">{row.wa_id}</span> },
  {
    key: "operador",
    label: "Operador asignado",
    render: (row) =>
      row.sin_asignar ? (
        <span className="font-bold text-brand-orange">Sin asignar</span>
      ) : (
        <span>
          {row.operador_nombre}
          {row.operador_email && (
            <span className="block text-[11px] text-muted-foreground">{row.operador_email}</span>
          )}
        </span>
      ),
  },
  {
    key: "desde",
    label: "Escribió",
    className: "w-28",
    render: (row) => <span className="tabular-nums">{formatHora(row.esperando_desde)}</span>,
  },
  {
    key: "texto",
    label: "Último mensaje",
    render: (row) => (
      <span className="line-clamp-2 text-muted-foreground">{row.ultimo_texto_cliente || "—"}</span>
    ),
  },
];

/** Pantalla /wati: todos los chats de WhatsApp esperando respuesta humana,
 * con semáforo de espera, operador asignado y último mensaje. Solo lectura
 * del estado sincronizado; "Sincronizar ahora" fuerza un ciclo contra WATI
 * (permiso wati.update). */
export function WatiPendientesDetail() {
  const { can } = useSession();
  const { resumen, pendientes, loading, error, refetch } = useWatiPendientes();
  const [sincronizando, setSincronizando] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);

  async function sincronizar() {
    setSincronizando(true);
    setSyncError(null);
    try {
      await watiApi.actualizar();
      refetch();
    } catch (err: unknown) {
      setSyncError(err instanceof Error ? err.message : "No se pudo sincronizar con WATI.");
    } finally {
      setSincronizando(false);
    }
  }

  const vencida = resumen ? sincronizacionVencida(resumen.sincronizado_at) : false;

  return (
    <div className="flex flex-col gap-5 px-7 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 font-heading text-[25px] font-extrabold text-foreground">
            <MessageCircle className="h-6 w-6 text-brand-orange" aria-hidden="true" />
            WhatsApp sin responder
          </h1>
          <p className="mt-0.5 font-body text-sm text-muted-foreground">
            Chats de WATI en los que el cliente escribió y ningún operador respondió todavía.
            {resumen && ` ${textoSincronizado(resumen.sincronizado_at).replace(/^s/, "S")}.`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {resumen?.inbox_url && (
            <a
              href={resumen.inbox_url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-body text-sm font-bold text-brand-orange hover:underline"
            >
              Abrir WATI ↗
            </a>
          )}
          {can("wati", "update") && (
            <BrandButton size="sm" variant="outline" loading={sincronizando} onClick={sincronizar}>
              <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
              Sincronizar ahora
            </BrandButton>
          )}
        </div>
      </div>

      {(vencida || syncError) && (
        <p className="flex items-center gap-2 rounded-[8px] bg-amber-500/10 px-3 py-2 font-body text-[13px] text-amber-600 dark:text-amber-400">
          <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
          {syncError ??
            "La sincronización con WATI está atrasada: el listado puede no reflejar los últimos mensajes."}
        </p>
      )}

      {resumen && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <BrandStatTile label="Esperando respuesta" value={resumen.total} tone="highlight" />
          <BrandStatTile label="Sin asignar" value={resumen.sin_asignar} />
          <BrandStatTile
            label="Espera más larga"
            value={resumen.max_minutos_esperando ? textoEspera(resumen.max_minutos_esperando).replace(/^hace /, "") : "—"}
          />
          <BrandStatTile
            label="Por operador"
            value={resumen.por_operador.map((o) => `${o.operador}: ${o.cantidad}`).join(" · ") || "—"}
          />
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-10">
          <Spinner />
        </div>
      ) : error ? (
        <p className="font-body text-sm text-destructive">{error}</p>
      ) : (
        <StatsTable
          title="Chats esperando respuesta"
          subtitle="Del más antiguo al más nuevo. Se actualiza solo cada minuto."
          columns={columns}
          rows={pendientes}
          rowKey={(row) => row.wa_id}
          emptyLabel="Sin chats esperando respuesta."
        />
      )}
    </div>
  );
}
