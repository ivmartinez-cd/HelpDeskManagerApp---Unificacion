"use client";

import { ChevronDown, ChevronRight, ClipboardList } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import type { PendientesResumen, PrestadorPendientes } from "../types/pendientes";
import { DashboardCard } from "@/features/home/components/dashboard-card";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";

function textoFrescura(updatedAt: string): string {
  const diffMs = Date.now() - new Date(updatedAt).getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 2) return "hace un momento";
  if (mins < 60) return `hace ${mins} min`;
  const hs = Math.round(mins / 60);
  return `hace ${hs} h`;
}

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
}: {
  resumen: PendientesResumen | null;
  loading: boolean;
  error: string | null;
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
      subtitle="Incidentes Finalizados sin cerrar"
      headerRight={
        resumen && total > 0 ? (
          <span className="rounded-full bg-amber-500/15 px-2 py-0.5 font-heading text-[12px] font-bold text-amber-400">
            {total}
          </span>
        ) : undefined
      }
      loading={loading}
      error={error}
    >
      {!resumen || total === 0 ? (
        <p className="pt-3 font-body text-[13px] text-muted-foreground">
          {resumen ? "Sin incidentes pendientes a cerrar." : "Sin datos disponibles."}
        </p>
      ) : (
        <>
          <ul className="mt-2.5 flex max-h-[220px] flex-col gap-1 overflow-y-auto pr-1">
            {resumen.por_operador.map((op) => {
              const prestadores = prestadoresPorOperador.get(op.operador_nombre) ?? [];
              const abierto = expandido === op.operador_nombre;
              return (
                <li key={op.operador_nombre}>
                  <button
                    type="button"
                    onClick={() => setExpandido(abierto ? null : op.operador_nombre)}
                    disabled={prestadores.length === 0}
                    className="flex w-full items-center justify-between gap-2 rounded-[6px] px-2 py-1.5 text-left hover:bg-white/[.03] disabled:cursor-default"
                  >
                    <span className="flex min-w-0 flex-1 items-center gap-1 truncate font-body text-[12px] text-foreground/80">
                      {prestadores.length > 0 &&
                        (abierto ? (
                          <ChevronDown className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden="true" />
                        ) : (
                          <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden="true" />
                        ))}
                      {op.operador_nombre}
                    </span>
                    <span className="shrink-0 rounded-full bg-amber-500/15 px-1.5 py-0.5 font-heading text-[11px] font-bold text-amber-400">
                      {op.cantidad}
                    </span>
                  </button>

                  {abierto && prestadores.length > 0 && (
                    <ul className="ml-4 flex flex-col gap-0.5 border-l border-border/60 pl-2.5">
                      {prestadores.map((pst) => (
                        <li
                          key={pst.id_tecnico}
                          className="flex items-center justify-between gap-2 rounded-[6px] px-2 py-1"
                        >
                          <span className="min-w-0 flex-1 truncate font-body text-[11px] text-muted-foreground">
                            {pst.tecnico}
                          </span>
                          <span className="shrink-0 rounded-full bg-amber-500/10 px-1.5 py-0.5 font-heading text-[10px] font-bold text-amber-400/90">
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

          <p className="mt-2 font-body text-[10px] text-muted-foreground/60">
            Actualizado {textoFrescura(resumen.updated_at)}
          </p>

          <Link href="/sla/pendientes-a-cerrar" className={brandButtonClasses() + " mt-3 w-full"}>
            Ver detalle →
          </Link>
        </>
      )}
    </DashboardCard>
  );
}
