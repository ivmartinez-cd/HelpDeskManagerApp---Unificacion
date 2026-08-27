"use client";

import { CalendarCheck2, CheckCircle2 } from "lucide-react";
import type {
  CalendarEvent,
  ClientesPendientesPeriodo,
  Operador,
  ResumenClientesOperador,
} from "@/features/contadores/types/calendario";
import { cn } from "@/shared/utils/cn";
import { fmtInt } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";
import { CardLink, CountBadge } from "./dashboard-card-bits";
import {
  ArrastreBlock,
  BucketsAntiguedad,
  PendientesLista,
  getCicloCierre,
  prepararPendientes,
} from "./facturacion-parts";

const TOP_LISTA = 6;

/** "Facturación sin cerrar" — fusión de las cards "Cierre mensual" y
 * "Pendientes por antigüedad" (rediseño 2026-08-22): las dos contaban la
 * misma historia (clientes procesados a los que faltan contadores; hasta que
 * el cliente responde no se cierra la facturación). Izquierda: estado del
 * ciclo de cierre (día 20) y arrastre; derecha: antigüedad y top de clientes. */
export function FacturacionSinCerrarCard({
  pendientes,
  operadores,
  resumen,
  pendientesPeriodoAnterior,
  pendientesPeriodoAnteriorLoading,
  pendientesPeriodoActual,
  loading,
  error,
  onRetry,
}: {
  pendientes: CalendarEvent[];
  operadores: Operador[];
  resumen: ResumenClientesOperador | null;
  pendientesPeriodoAnterior: ClientesPendientesPeriodo | null;
  pendientesPeriodoAnteriorLoading: boolean;
  pendientesPeriodoActual: CalendarEvent[] | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}) {
  const lista = prepararPendientes(pendientes, operadores);
  const sinCerrar = lista.length;
  // Solo alimenta el número grande del arrastre (incluye a los que todavía
  // no llegaron a su fecha); el desglose de abajo sigue siendo nada más el
  // atraso real (`lista`) — mezclar los dos ahí lo volvía inútil, dominado
  // por el bucket "Sin vencer".
  const periodoActual = pendientesPeriodoActual?.length ?? null;
  const total = resumen?.total_clientes ?? null;
  const cerrados = total !== null ? Math.max(0, total - sinCerrar) : null;
  const pct = cerrados !== null && total && total > 0 ? (cerrados / total) * 100 : null;
  const { enArrastre, labelProximoCierre, diasParaCierre } = getCicloCierre(new Date());
  const urgente = !enArrastre && sinCerrar > 0 && diasParaCierre <= 5;
  const viejos = lista.filter((p) => p.dias >= 10).length;

  return (
    <DashboardCard
      icon={CalendarCheck2}
      title="Facturación sin cerrar"
      subtitle={`Contadores del mes · cierre el ${labelProximoCierre}`}
      loading={loading}
      error={error}
      onRetry={onRetry}
      bodyClassName="@container"
      headerRight={
        sinCerrar > 0 ? (
          <CountBadge value={sinCerrar} tone={viejos > 0 || urgente ? "bad" : "warn"} />
        ) : (
          <CountBadge value="al día" tone="ok" />
        )
      }
      footer={
        <>
          <CardLink href="/contadores/anexos-pendientes">Ver anexos sin facturar →</CardLink>
          <CardLink href="/contadores/calendario">Ver calendario →</CardLink>
        </>
      }
    >
      <div className="grid gap-3 @sm:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
        <div className="flex flex-col gap-2">
          {enArrastre ? (
            <>
              {periodoActual === 0 ? (
                <div className="flex items-center gap-2 pt-1">
                  <CheckCircle2 className="h-5 w-5 shrink-0 text-success" />
                  <span className="font-heading text-[14px] font-bold text-success">
                    Todos cerrados
                  </span>
                </div>
              ) : (
                <Numero
                  valor={periodoActual}
                  texto={`${periodoActual === 1 ? "cliente por cerrar" : "clientes por cerrar"} antes del ${labelProximoCierre}`}
                  tone="text-foreground"
                />
              )}
              <span className="font-body text-[11.5px] text-muted-foreground">
                Nuevo período en curso · faltan {diasParaCierre} {diasParaCierre === 1 ? "día" : "días"}
              </span>
              <ArrastreBlock
                data={pendientesPeriodoAnterior}
                loading={pendientesPeriodoAnteriorLoading}
              />
            </>
          ) : sinCerrar === 0 ? (
            <div className="flex items-center gap-2 pt-1">
              <CheckCircle2 className="h-5 w-5 shrink-0 text-success" />
              <span className="font-heading text-[14px] font-bold text-success">Todos cerrados</span>
            </div>
          ) : (
            <>
              <Numero
                valor={sinCerrar}
                texto={`${sinCerrar === 1 ? "cliente sin cerrar" : "clientes sin cerrar"}${
                  total !== null ? ` de ${fmtInt(total)}` : ""
                }`}
                tone={urgente ? "text-destructive" : "text-warning-foreground dark:text-warning"}
              />
              {pct !== null && (
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-2">
                  <div
                    className="h-full rounded-full bg-brand-orange transition-all"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              )}
              <span className="font-body text-[11.5px] text-muted-foreground">
                {diasParaCierre > 0
                  ? `${diasParaCierre} ${diasParaCierre === 1 ? "día" : "días"} para el cierre`
                  : "Cierre hoy"}
                {pct !== null && ` · ${fmtInt(Math.round(pct))} % cerrado`}
              </span>
            </>
          )}
        </div>
        {sinCerrar > 0 && (
          <div className="flex min-w-0 flex-col gap-2.5">
            <BucketsAntiguedad pendientes={lista} />
            <PendientesLista pendientes={lista} top={TOP_LISTA} />
          </div>
        )}
      </div>
    </DashboardCard>
  );
}

function Numero({ valor, texto, tone }: { valor: number | null; texto: string; tone: string }) {
  return (
    <div className="flex items-baseline gap-1.5">
      {valor !== null && (
        <span className={cn("font-heading text-[28px] font-extrabold leading-none tabular-nums", tone)}>
          {fmtInt(valor)}
        </span>
      )}
      <span className="font-body text-[12.5px] text-muted-foreground">{texto}</span>
    </div>
  );
}
