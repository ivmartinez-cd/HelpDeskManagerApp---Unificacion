"use client";

import { FileText, RotateCw } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { liquidacionesApi } from "@/features/liquidaciones/api/liquidaciones-api";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import { fmtInt } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";
import { OperadorDonut } from "./operador-donut";

const PALETTE = [
  "#e07c39", // brand orange
  "#6b9bb8", // blue
  "#c4a35a", // amber
  "#7a9b7a", // green
  "#9b7ab8", // purple
  "#b87a7a", // red
];

export function LiquidacionesPendientesCard({
  data,
  loading,
  error,
  onSynced,
}: {
  data: { pendientes: number; porPrestador: { nombreCorto: string; count: number }[] } | null;
  loading: boolean;
  error: string | null;
  onSynced?: () => void;
}) {
  const total = data?.pendientes ?? 0;
  const [syncing, setSyncing] = useState(false);

  const rows = (data?.porPrestador ?? []).map((p, i) => ({
    id: p.nombreCorto,
    nombre: p.nombreCorto,
    color: PALETTE[i % PALETTE.length],
    valor: p.count,
  }));

  const handleSincronizar = async () => {
    setSyncing(true);
    try {
      const res = await liquidacionesApi.sincronizar();
      const revisadas = res.reconciliadas > 0
        ? ` (${res.reconciliadas} revisada${res.reconciliadas !== 1 ? "s" : ""} contra AyC${res.estadosActualizados > 0 ? `, ${res.estadosActualizados} con estado actualizado` : ""})`
        : "";
      const detalle = `${res.creadas} nueva${res.creadas !== 1 ? "s" : ""}, ${res.yaExistentes} ya existentes${revisadas}${res.sinPrestador > 0 ? `, ${res.sinPrestador} sin prestador vinculado` : ""}${res.anuladas > 0 ? `, ${res.anuladas} anulada${res.anuladas !== 1 ? "s" : ""} en AyC eliminada${res.anuladas !== 1 ? "s" : ""}` : ""}`;
      if (res.fallidas > 0) {
        toast.warning(
          `Sync con fallas — ${detalle}, ${res.fallidas} con detalle SOAP fallido (se reintentan en el próximo sync)`,
        );
      } else {
        toast.success(`Sync OK — ${detalle}`);
      }
      if (res.creadas > 0 || res.reconciliadas > 0 || res.anuladas > 0) onSynced?.();
    } catch {
      toast.error("Error al sincronizar con Canal Directo");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <DashboardCard
      icon={FileText}
      title="Liquidaciones sin aprobar"
      subtitle="Pendientes de aprobación"
      loading={loading}
      error={error}
      headerRight={
        <div className="flex shrink-0 items-center gap-1.5">
          <button
            type="button"
            onClick={() => void handleSincronizar()}
            disabled={syncing}
            title="Sincronizar CD"
            aria-label="Sincronizar CD"
            className="flex h-6 w-6 items-center justify-center rounded-[6px] border border-border text-muted-foreground transition-colors hover:border-brand-orange/60 hover:text-brand-orange disabled:opacity-50"
          >
            <RotateCw className={cn("h-3.5 w-3.5", syncing && "animate-spin")} />
          </button>
          {data && (
            <span className="font-heading text-[15px] font-extrabold text-amber-500">
              {fmtInt(total)}
            </span>
          )}
        </div>
      }
    >
      {total === 0 ? (
        <span className="pt-3 font-body text-[13px] text-muted-foreground">
          No hay liquidaciones pendientes de aprobación.
        </span>
      ) : (
        <>
          <OperadorDonut
            rows={rows}
            total={total}
            centerSub="pendientes"
            tooltipUnidad="liquidaciones"
          />
          <Link href="/liquidaciones" className={cn(brandButtonClasses(), "mt-2.5 w-full")}>
            Ver liquidaciones →
          </Link>
        </>
      )}
    </DashboardCard>
  );
}
