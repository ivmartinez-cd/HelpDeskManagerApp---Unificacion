"use client";

import { Gauge } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { slaApi } from "../api/sla-api";
import type { SlaResumen } from "../types/sla";
import { useSession } from "@/services/session-provider";
import { Spinner } from "@/shared/components/ui/spinner";

function currentPeriodo(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}${month}`;
}

export function SlaSummaryCard() {
  const { modules } = useSession();
  const canView = modules.some((m) => m.key === "sla");

  const [resumen, setResumen] = useState<SlaResumen | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!canView) {
      setLoading(false);
      return;
    }
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
    <div className="flex w-full max-w-sm flex-col gap-3 rounded-[12px] border border-border bg-card p-5">
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
        <div className="flex flex-col gap-2">
          <div className="flex items-end justify-between gap-4">
            <div className="flex flex-col">
              <span className="font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
                Correctos
              </span>
              <span className="font-heading text-[22px] font-extrabold leading-tight text-brand-orange">
                {resumen.pct_correctos.toLocaleString("es-AR", { maximumFractionDigits: 1 })}%
              </span>
              <span className="font-body text-[12px] text-muted-foreground">
                {resumen.correctos.toLocaleString("es-AR")} de {resumen.total.toLocaleString("es-AR")}
              </span>
            </div>
            <div className="flex flex-col items-end">
              <span className="font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
                Vencidos
              </span>
              <span className="font-heading text-[22px] font-extrabold leading-tight text-[#dc2626] dark:text-[#f87171]">
                {resumen.pct_vencidos.toLocaleString("es-AR", { maximumFractionDigits: 1 })}%
              </span>
              <span className="font-body text-[12px] text-muted-foreground">
                {resumen.vencidos.toLocaleString("es-AR")} incidentes
              </span>
            </div>
          </div>
          <Link
            href="/sla"
            className="mt-1 font-body text-[12.5px] text-brand-orange hover:underline"
          >
            Ver detalle →
          </Link>
        </div>
      )}
    </div>
  );
}
