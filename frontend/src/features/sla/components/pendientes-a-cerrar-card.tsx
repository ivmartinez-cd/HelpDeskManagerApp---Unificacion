"use client";

import { ChevronDown, ChevronRight, ClipboardList } from "lucide-react";
import { useMemo, useState } from "react";
import type { PendientesResumen, PrestadorPendientes } from "../types/pendientes";
import { DashboardCard } from "@/features/home/components/dashboard-card";
import {
  CardEmpty,
  CardLink,
  CountBadge,
  Freshness,
} from "@/features/home/components/dashboard-card-bits";

/** El resumen lo recalcula un job del backend; más de un día sin actualizar
 * es señal de job caído, no de "no hubo cambios". */
const STALE_MIN = 24 * 60;

function agruparPorOperador(
  porPrestador: PrestadorPendientes[],
): Map<string, PrestadorPendientes[]> {
  const grupos = new Map<string, PrestadorPendientes[]>();
  for (const prestador of porPrestador) {
    const clave = prestador.operador_nombre ?? "";
    const lista = grupos.get(clave);
    if (lista) lista.push(prestador);
    else grupos.set(clave, [prestador]);
  }
  return grupos;
}

export function PendientesACerrarCard({
  resumen,
  loading,
  error,
  onRetry,
}: {
  resumen: PendientesResumen | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}) {
  const total = resumen?.total ?? 0;
  const [expandido, setExpandido] = useState<string | null>(null);
  const prestadoresPorOperador = useMemo(
    () => agruparPorOperador(resumen?.por_prestador ?? []),
    [resumen],
  );

  return (
    <DashboardCard
      icon={ClipboardList}
      title="Pendientes a cerrar"
      subtitle="Incidentes finalizados sin cerrar"
      headerRight={resumen && total > 0 ? <CountBadge value={total} tone="warn" /> : undefined}
      loading={loading}
      error={error}
      onRetry={onRetry}
      footer={
        <>
          {resumen && <Freshness at={resumen.updated_at} staleAfterMin={STALE_MIN} />}
          <CardLink href="/sla/pendientes-a-cerrar">Ver detalle →</CardLink>
        </>
      }
    >
      {!resumen || total === 0 ? (
        <CardEmpty>{resumen ? "Sin incidentes pendientes a cerrar." : "Sin datos disponibles."}</CardEmpty>
      ) : (
        <ul className="flex flex-col gap-0.5">
          {resumen.por_operador.map((op) => {
            const prestadores = prestadoresPorOperador.get(op.operador_nombre) ?? [];
            const abierto = expandido === op.operador_nombre;
            return (
              <li key={op.operador_nombre}>
                <button
                  type="button"
                  onClick={() => setExpandido(abierto ? null : op.operador_nombre)}
                  disabled={prestadores.length === 0}
                  className="flex w-full items-center justify-between gap-2 rounded-[6px] px-1.5 py-1 text-left hover:bg-muted/60 disabled:cursor-default"
                >
                  <span className="flex min-w-0 flex-1 items-center gap-1 truncate font-body text-[12.5px] font-semibold text-foreground/80">
                    {prestadores.length > 0 &&
                      (abierto ? (
                        <ChevronDown className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden="true" />
                      ) : (
                        <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden="true" />
                      ))}
                    {op.operador_nombre}
                  </span>
                  <span className="shrink-0 font-heading text-[12px] font-bold tabular-nums text-foreground">
                    {op.cantidad}
                  </span>
                </button>

                {abierto && prestadores.length > 0 && (
                  <ul className="ml-3.5 flex flex-col gap-0.5 border-l border-border/60 pl-2.5">
                    {prestadores.map((pst) => (
                      <li
                        key={pst.id_tecnico}
                        className="flex items-center justify-between gap-2 rounded-[6px] px-1.5 py-0.5"
                      >
                        <span className="min-w-0 flex-1 truncate font-body text-[11.5px] text-muted-foreground">
                          {pst.tecnico}
                        </span>
                        <span className="shrink-0 font-heading text-[11px] font-bold tabular-nums text-muted-foreground">
                          {pst.cantidad}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </DashboardCard>
  );
}
