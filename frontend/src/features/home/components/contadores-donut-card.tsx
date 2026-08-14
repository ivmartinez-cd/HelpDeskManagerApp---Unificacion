"use client";

import { Users } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { ClienteCruceModal } from "@/features/contadores/components/cliente-cruce-modal";
import type { ResumenClientesOperador } from "@/features/contadores/types/calendario";
import { useSession } from "@/services/session-provider";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import { FALLBACK_COLOR, fmtInt } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";
import { OperadorDonut } from "./operador-donut";

export function ContadoresDonutCard({
  resumen,
  loading,
  error,
  onResolved,
}: {
  resumen: ResumenClientesOperador | null;
  loading: boolean;
  error: string | null;
  onResolved: () => void;
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
      detalle: `${f.clientes} ${f.clientes === 1 ? "cliente" : "clientes"}`,
      color: f.operador_color ?? FALLBACK_COLOR,
      valor: f.impresoras ?? 0,
    }))
    .sort((a, b) => b.valor - a.valor);
  const sinCruce = [...new Set(filas.flatMap((f) => f.sin_cruce))].sort();

  return (
    <DashboardCard
      icon={Users}
      title="Contadores por operador"
      subtitle="Clientes e impresoras del mes"
      loading={loading}
      error={error}
      headerRight={
        conImpresoras && resumen ? (
          <span className="shrink-0 font-heading text-[15px] font-extrabold text-brand-orange">
            {fmtInt(resumen.total_impresoras as number)}
          </span>
        ) : undefined
      }
    >
      {filas.length === 0 ? (
        <span className="pt-3 font-body text-[13px] text-muted-foreground">
          No hay clientes planificados en el calendario.
        </span>
      ) : (
        <>
          {conImpresoras ? (
            <OperadorDonut
              rows={rows}
              total={resumen?.total_impresoras ?? 0}
              centerSub="impresoras"
              tooltipUnidad="impresoras"
            />
          ) : (
            // Siges caído: sin impresoras no hay dona — degrada a la lista de
            // clientes por operador (misma decisión que la card anterior).
            <div className="flex flex-col gap-[7px] pt-3">
              {rows.map((r) => (
                <div key={r.id} className="flex items-center gap-2">
                  <span
                    className="h-[9px] w-[9px] shrink-0 rounded-[3px]"
                    style={{ background: r.color }}
                  />
                  <span className="min-w-0 flex-1 truncate font-body text-[12.5px] font-semibold text-foreground/70">
                    {r.nombre}
                  </span>
                  <span className="shrink-0 font-body text-[12px] font-semibold text-muted-foreground">
                    {r.detalle}
                  </span>
                </div>
              ))}
              <span className="font-body text-[11px] text-amber-600">
                Siges no respondió: se muestran solo los clientes, sin impresoras.
              </span>
            </div>
          )}
          {sinCruce.length > 0 && (
            <div className="mt-2.5 flex items-center justify-between gap-2">
              <span className="font-body text-[11px] text-muted-foreground">
                {sinCruce.length} {sinCruce.length === 1 ? "cliente" : "clientes"} sin cruce con
                Siges — sus impresoras no están sumadas.
              </span>
              {canManage && (
                <button
                  type="button"
                  onClick={() => setResolviendo(true)}
                  className="shrink-0 rounded-full bg-amber-500/[0.15] px-2 py-0.5 font-body text-[11px] font-semibold text-amber-600 hover:bg-amber-500/[0.25]"
                >
                  Resolver
                </button>
              )}
            </div>
          )}
          <Link href="/contadores/calendario" className={cn(brandButtonClasses(), "mt-2.5 w-full")}>
            Ver calendario →
          </Link>
        </>
      )}

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
