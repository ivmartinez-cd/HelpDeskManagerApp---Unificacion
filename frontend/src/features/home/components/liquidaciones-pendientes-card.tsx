"use client";

import { FileText, RotateCw } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { liquidacionesApi } from "@/features/liquidaciones/api/liquidaciones-api";
import { cn } from "@/shared/utils/cn";
import type { LiquidacionesPendientes } from "../hooks/use-inicio-data";
import { BRAND_ORANGE } from "../utils/chart-theme";
import { fmtInt } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";
import { BarRow, CardEmpty, CardLink, CountBadge } from "./dashboard-card-bits";

function resumenSync(res: Awaited<ReturnType<typeof liquidacionesApi.sincronizar>>): string {
  const revisadas =
    res.reconciliadas > 0
      ? ` (${res.reconciliadas} revisada${res.reconciliadas !== 1 ? "s" : ""} contra AyC${
          res.estadosActualizados > 0 ? `, ${res.estadosActualizados} con estado actualizado` : ""
        })`
      : "";
  return `${res.creadas} nueva${res.creadas !== 1 ? "s" : ""}, ${res.yaExistentes} ya existentes${revisadas}${
    res.sinPrestador > 0 ? `, ${res.sinPrestador} sin prestador vinculado` : ""
  }${
    res.anuladas > 0
      ? `, ${res.anuladas} anulada${res.anuladas !== 1 ? "s" : ""} en AyC eliminada${res.anuladas !== 1 ? "s" : ""}`
      : ""
  }`;
}

/** Liquidaciones sin aprobar: barras por prestador (un solo matiz: la
 * longitud compara, el color no hace falta) en vez de dona con paleta propia. */
export function LiquidacionesPendientesCard({
  data,
  loading,
  error,
  onSynced,
  onRetry,
}: {
  data: LiquidacionesPendientes | null;
  loading: boolean;
  error: string | null;
  onSynced?: () => void;
  onRetry?: () => void;
}) {
  const total = data?.pendientes ?? 0;
  const [syncing, setSyncing] = useState(false);
  const rows = [...(data?.porPrestador ?? [])].sort((a, b) => b.count - a.count);
  const max = Math.max(1, ...rows.map((r) => r.count));

  const handleSincronizar = async () => {
    setSyncing(true);
    try {
      const res = await liquidacionesApi.sincronizar();
      const detalle = resumenSync(res);
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
      title="Liquidaciones"
      subtitle="Pendientes de aprobación"
      loading={loading}
      error={error}
      onRetry={onRetry}
      headerRight={
        <>
          <button
            type="button"
            onClick={() => void handleSincronizar()}
            disabled={syncing}
            title="Sincronizar CD"
            aria-label="Sincronizar CD"
            className="flex h-7 w-7 items-center justify-center rounded-[8px] border border-border text-muted-foreground transition-colors hover:border-brand-orange/60 hover:text-brand-orange disabled:opacity-50"
          >
            <RotateCw className={cn("h-3.5 w-3.5", syncing && "animate-spin")} />
          </button>
          {data && <CountBadge value={fmtInt(total)} tone={total > 0 ? "warn" : "ok"} />}
        </>
      }
      footer={<CardLink href="/liquidaciones">Ver liquidaciones →</CardLink>}
    >
      {total === 0 ? (
        <CardEmpty>No hay liquidaciones pendientes de aprobación.</CardEmpty>
      ) : (
        <div className="flex flex-col gap-1.5">
          {rows.map((r) => (
            <BarRow
              key={r.nombreCorto}
              color={BRAND_ORANGE}
              label={r.nombreCorto}
              value={fmtInt(r.count)}
              widthPct={(r.count / max) * 100}
            />
          ))}
        </div>
      )}
    </DashboardCard>
  );
}
