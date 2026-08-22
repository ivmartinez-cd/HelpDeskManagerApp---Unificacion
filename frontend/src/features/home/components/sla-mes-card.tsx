"use client";

import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";
import { Gauge, RotateCw } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useMemo, useState } from "react";
import { Line } from "react-chartjs-2";
import { toast } from "sonner";
import { slaApi } from "@/features/sla/api/sla-api";
import { useSession } from "@/services/session-provider";
import { cn } from "@/shared/utils/cn";
import type { SlaHistoria } from "../hooks/use-inicio-data";
import { chartTheme } from "../utils/chart-theme";
import { fmtInt, fmtPct, periodoLabel } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";
import { CardEmpty, CardLink, MiniStat } from "./dashboard-card-bits";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip);

function Tendencia({ historia }: { historia: SlaHistoria }) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setMounted(true), []);
  const tema = useMemo(() => chartTheme(), [resolvedTheme, mounted]); // eslint-disable-line react-hooks/exhaustive-deps

  const puntos = historia.resumenes
    .map((r, i) => (r && r.total > 0 ? { label: periodoLabel(historia.periodos[i]), pct: r.pct_correctos } : null))
    .filter((p): p is { label: string; pct: number } => p !== null);
  if (puntos.length < 2) return null;
  const min = Math.floor(Math.min(...puntos.map((p) => p.pct))) - 1;
  const max = Math.ceil(Math.max(...puntos.map((p) => p.pct)));

  return (
    <div className="flex min-h-0 flex-1 flex-col short:hidden">
      <div className="mb-1 font-heading text-[10.5px] font-bold uppercase tracking-[.05em] text-muted-foreground">
        Tendencia · últimos {puntos.length} meses
      </div>
      {/* Tope de alto: en monitores 2K al 100 % la card es muy alta y la
          sparkline estirada se veía desproporcionada. */}
      <div className="relative max-h-[140px] min-h-[40px] flex-1">
        <Line
          key={resolvedTheme}
          data={{
            labels: puntos.map((p) => p.label),
            datasets: [
              {
                data: puntos.map((p) => p.pct),
                borderColor: tema.orange,
                backgroundColor: (ctx) => {
                  const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, 56);
                  g.addColorStop(0, "rgba(247,148,29,.35)");
                  g.addColorStop(1, "rgba(247,148,29,0)");
                  return g;
                },
                fill: true,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                pointBackgroundColor: tema.orange,
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: { callbacks: { label: (c) => ` ${fmtPct(c.raw as number)}%` } },
            },
            scales: {
              x: { grid: { display: false }, ticks: { color: tema.tick, font: { size: 10 } } },
              y: { display: false, min, max },
            },
          }}
        />
      </div>
    </div>
  );
}

/** SLA del mes: un porcentaje es un número + barra, no una dona de dos
 * gajos (NN/g): valor grande, barra correctos/vencidos, comparación con el
 * mes anterior y tendencia real de 6 meses. */
export function SlaMesCard({
  historia,
  loading,
  error,
  onSynced,
  onRetry,
}: {
  historia: SlaHistoria | null;
  loading: boolean;
  error: string | null;
  onSynced?: () => void;
  onRetry?: () => void;
}) {
  const { user, can } = useSession();
  const canUpdate = user.isSuperadmin || can("sla", "update");
  const [syncing, setSyncing] = useState(false);

  const actual = historia?.resumenes[historia.resumenes.length - 1] ?? null;
  const anterior = historia?.resumenes[historia.resumenes.length - 2] ?? null;
  const variacion =
    actual && anterior && anterior.total > 0 ? actual.pct_correctos - anterior.pct_correctos : null;

  const handleSincronizar = async () => {
    const periodo = historia?.periodos[historia.periodos.length - 1];
    if (!periodo) return;
    setSyncing(true);
    try {
      await slaApi.refreshResumen(periodo);
      toast.success("SLA actualizado contra MERCURIO");
      onSynced?.();
    } catch {
      toast.error("Error al actualizar el SLA");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <DashboardCard
      icon={Gauge}
      title="SLA del mes"
      subtitle="Cumplimiento de acuerdos"
      loading={loading}
      error={error}
      onRetry={onRetry}
      headerRight={
        <button
          type="button"
          onClick={() => void handleSincronizar()}
          disabled={syncing || !historia || !canUpdate}
          title={canUpdate ? "Actualizar SLA (consulta completa a MERCURIO, ~40 s)" : "Sin permiso para actualizar"}
          aria-label="Actualizar SLA"
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[8px] border border-border text-muted-foreground transition-colors hover:border-brand-orange/60 hover:text-brand-orange disabled:opacity-50"
        >
          <RotateCw className={cn("h-3.5 w-3.5", syncing && "animate-spin")} />
        </button>
      }
      footer={<CardLink href="/sla">Ver detalle →</CardLink>}
    >
      {!actual || actual.total === 0 ? (
        <CardEmpty>Sin incidentes en el período actual.</CardEmpty>
      ) : (
        <div className="flex min-h-0 flex-1 flex-col gap-2.5">
          <div className="flex items-baseline gap-2">
            <span className="font-heading text-[28px] font-extrabold leading-none tabular-nums text-foreground">
              {fmtPct(actual.pct_correctos)}%
            </span>
            <span className="font-body text-[12px] text-muted-foreground">
              {fmtInt(actual.correctos)} de {fmtInt(actual.total)} incidentes en término
            </span>
          </div>
          <div
            className="flex h-2 w-full overflow-hidden rounded-full bg-surface-2"
            role="img"
            aria-label={`${fmtPct(actual.pct_correctos)}% correctos, ${fmtInt(actual.vencidos)} vencidos`}
          >
            <span className="h-full bg-brand-orange" style={{ width: `${actual.pct_correctos}%` }} />
            <span className="h-full bg-destructive" style={{ width: `${actual.pct_vencidos}%` }} />
          </div>
          <div className="grid grid-cols-3 gap-1.5">
            <MiniStat label="Vencidos" value={fmtInt(actual.vencidos)} className="text-destructive" />
            <MiniStat
              label="Mes ant."
              value={anterior && anterior.total > 0 ? `${fmtPct(anterior.pct_correctos)}%` : "—"}
              className="text-foreground/70"
            />
            <MiniStat
              label="Variación"
              value={
                variacion === null ? "—" : `${variacion >= 0 ? "▲" : "▼"} ${fmtPct(Math.abs(variacion))}`
              }
              className={variacion === null ? undefined : variacion >= 0 ? "text-success" : "text-destructive"}
            />
          </div>
          {historia && <Tendencia historia={historia} />}
        </div>
      )}
    </DashboardCard>
  );
}
