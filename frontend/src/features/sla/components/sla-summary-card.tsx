"use client";

import { ArcElement, Chart as ChartJS, Tooltip } from "chart.js";
import { Gauge } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Doughnut } from "react-chartjs-2";
import { slaApi } from "../api/sla-api";
import type { SlaResumen } from "../types/sla";
import { useSession } from "@/services/session-provider";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { cn } from "@/shared/utils/cn";

ChartJS.register(ArcElement, Tooltip);

const ORANGE = "#F7941D";
const RED = "#ef4444";

function currentPeriodo(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}${month}`;
}

function formatPct(value: number): string {
  return value.toLocaleString("es-AR", { maximumFractionDigits: 2 });
}

/** Dona de cumplimiento del mes — Patrón nuevo acordado con el usuario a
 * partir del mockup que pasó (2026-08-12): centro con el % de correctos,
 * leyenda de dos columnas debajo, botón "Ver detalle" de ancho completo. */
function ComplianceDonut({ resumen }: { resumen: SlaResumen }) {
  const data = {
    labels: ["Correctos", "Vencidos"],
    datasets: [
      {
        data: [resumen.correctos, resumen.vencidos],
        backgroundColor: [ORANGE, RED],
        borderWidth: 0,
      },
    ],
  };

  return (
    <div className="relative mx-auto h-[168px] w-[168px]">
      <Doughnut
        data={data}
        options={{
          cutout: "74%",
          plugins: { tooltip: { enabled: false }, legend: { display: false } },
          animation: { duration: 400 },
        }}
      />
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-heading text-[26px] font-extrabold text-foreground">
          {formatPct(resumen.pct_correctos)}%
        </span>
        <span className="font-body text-[11px] text-muted-foreground">correctos</span>
      </div>
    </div>
  );
}

function ComplianceLegend({ resumen }: { resumen: SlaResumen }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="flex flex-col gap-0.5">
        <span className="flex items-center gap-1.5 font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: ORANGE }} />
          Correctos
        </span>
        <span className="font-heading text-[20px] font-extrabold text-brand-orange">
          {formatPct(resumen.pct_correctos)}%
        </span>
        <span className="font-body text-[12px] text-muted-foreground">
          {resumen.correctos.toLocaleString("es-AR")} de {resumen.total.toLocaleString("es-AR")}
        </span>
      </div>
      <div className="flex flex-col gap-0.5 items-end text-right">
        <span className="flex items-center gap-1.5 font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: RED }} />
          Vencidos
        </span>
        <span className="font-heading text-[20px] font-extrabold" style={{ color: RED }}>
          {formatPct(resumen.pct_vencidos)}%
        </span>
        <span className="font-body text-[12px] text-muted-foreground">
          {resumen.vencidos.toLocaleString("es-AR")} incidentes
        </span>
      </div>
    </div>
  );
}

export function SlaSummaryCard() {
  const { modules } = useSession();
  const canView = modules.some((m) => m.key === "sla");

  const [resumen, setResumen] = useState<SlaResumen | null>(null);
  const [loading, setLoading] = useState<boolean>(canView);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!canView) return;
    slaApi
      .getResumen(currentPeriodo())
      .then(setResumen)
      .catch((err: unknown) => {
        console.error("Error al cargar el resumen SLA:", err);
        setError(err instanceof Error ? err.message : "No se pudo cargar el resumen SLA.");
      })
      .finally(() => setLoading(false));
  }, [canView]);

  if (!canView) return null;

  return (
    <div className="flex w-full max-w-sm flex-col gap-4 rounded-[12px] border border-border bg-card p-5">
      <div className="flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-[9px] bg-brand-orange/[0.12] text-brand-orange">
          <Gauge className="h-4 w-4" />
        </span>
        <div className="flex flex-col">
          <h2 className="font-heading text-[14.5px] font-bold text-foreground">SLA del mes</h2>
          <span className="font-body text-[12.5px] text-muted-foreground">
            Cumplimiento de acuerdos de servicio
          </span>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-4">
          <Spinner />
        </div>
      ) : error ? (
        <span className="font-body text-[13px] text-destructive">{error}</span>
      ) : !resumen || resumen.total === 0 ? (
        <span className="font-body text-[13px] text-muted-foreground">
          Sin incidentes en el período actual.
        </span>
      ) : (
        <div className="flex flex-col gap-4">
          <ComplianceDonut resumen={resumen} />
          <ComplianceLegend resumen={resumen} />
          <Link href="/sla" className={cn(brandButtonClasses(), "w-full")}>
            Ver detalle →
          </Link>
        </div>
      )}
    </div>
  );
}
