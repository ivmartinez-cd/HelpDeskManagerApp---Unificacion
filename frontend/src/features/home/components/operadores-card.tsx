"use client";

import { Users } from "lucide-react";
import { useState } from "react";
import { ClienteCruceModal } from "@/features/contadores/components/cliente-cruce-modal";
import type {
  CalendarEvent,
  Operador,
  ResumenClientesOperador,
} from "@/features/contadores/types/calendario";
import { useSession } from "@/services/session-provider";
import { FALLBACK_COLOR, fmtInt, fmtPct } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";
import { BarRow, CardEmpty, CardLink } from "./dashboard-card-bits";
import { HeatmapSemana } from "./heatmap-semana";

/** "Operadores" — fusión de "Contadores por operador" (antes dona) y
 * "Clientes por operador · semana" (heatmap): mismo eje, el operador. Las
 * impresoras del mes se comparan con barras ordenadas (longitud, no ángulo);
 * el heatmap muestra la carga por día. La parte de barras requiere la
 * feature `contadores-card-operadores` (ADR-032); el heatmap, el módulo. */
export function OperadoresCard({
  resumen,
  resumenLoading,
  resumenError,
  onResolved,
  mostrarOperadores,
  semana,
  operadores,
  loading,
  error,
  onRetry,
}: {
  resumen: ResumenClientesOperador | null;
  resumenLoading: boolean;
  resumenError: string | null;
  onResolved: () => void;
  mostrarOperadores: boolean;
  semana: CalendarEvent[];
  operadores: Operador[];
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}) {
  const { user, can } = useSession();
  const canManage = user.isSuperadmin || can("contadores", "manage");
  const [resolviendo, setResolviendo] = useState(false);

  const filas = resumen?.operadores ?? [];
  const conImpresoras = resumen?.total_impresoras != null;
  const rows = filas
    .map((f) => ({
      id: f.operador_id,
      nombre: f.operador_nombre,
      clientes: f.clientes,
      color: f.operador_color ?? FALLBACK_COLOR,
      valor: conImpresoras ? (f.impresoras ?? 0) : f.clientes,
    }))
    .sort((a, b) => b.valor - a.valor);
  const totalValor = rows.reduce((s, r) => s + r.valor, 0);
  const max = Math.max(1, ...rows.map((r) => r.valor));
  const sinCruce = [...new Set(filas.flatMap((f) => f.sin_cruce))].sort();

  return (
    <DashboardCard
      icon={Users}
      title="Operadores"
      subtitle={
        mostrarOperadores ? "Impresoras del mes y clientes por día" : "Clientes por día según calendario"
      }
      loading={loading || (mostrarOperadores && resumenLoading)}
      error={error ?? (mostrarOperadores ? resumenError : null)}
      onRetry={onRetry}
      bodyClassName="@container"
      headerRight={
        mostrarOperadores && conImpresoras && resumen ? (
          <span className="font-heading text-[14px] font-extrabold tabular-nums text-brand-orange">
            {fmtInt(resumen.total_impresoras as number)}
            <span className="ml-1 font-body text-[11px] font-normal text-muted-foreground">
              impresoras
            </span>
          </span>
        ) : undefined
      }
      footer={<CardLink href="/contadores/calendario">Ver calendario →</CardLink>}
    >
      <div className="grid gap-3 @md:grid-cols-2">
        {mostrarOperadores && (
          <div className="flex min-w-0 flex-col gap-1.5">
            {rows.length === 0 ? (
              <CardEmpty>No hay clientes planificados en el calendario.</CardEmpty>
            ) : (
              rows.map((r) => (
                <BarRow
                  key={r.id}
                  color={r.color}
                  label={r.nombre}
                  detail={`${r.clientes} cl.`}
                  value={fmtInt(r.valor)}
                  pct={totalValor > 0 ? `${fmtPct(Math.round((r.valor / totalValor) * 1000) / 10)}%` : undefined}
                  widthPct={(r.valor / max) * 100}
                />
              ))
            )}
            {rows.length > 0 && !conImpresoras && (
              <span className="font-body text-[11px] text-warning-foreground dark:text-warning">
                Siges no respondió: se muestran clientes, no impresoras.
              </span>
            )}
            {sinCruce.length > 0 && (
              <div className="flex items-center justify-between gap-2">
                <span className="font-body text-[11px] text-muted-foreground">
                  {sinCruce.length} {sinCruce.length === 1 ? "cliente" : "clientes"} sin cruce — sus
                  impresoras no están sumadas.
                </span>
                {canManage && (
                  <button
                    type="button"
                    onClick={() => setResolviendo(true)}
                    className="shrink-0 rounded-full bg-warning/20 px-2 py-0.5 font-body text-[11px] font-semibold text-warning-foreground hover:bg-warning/30 dark:text-warning"
                  >
                    Resolver
                  </button>
                )}
              </div>
            )}
          </div>
        )}
        <div className="min-w-0">
          <HeatmapSemana eventos={semana} operadores={operadores} />
        </div>
      </div>

      {resolviendo && (
        <ClienteCruceModal
          clientes={sinCruce}
          onClose={() => setResolviendo(false)}
          onSaved={onResolved}
        />
      )}
    </DashboardCard>
  );
}
