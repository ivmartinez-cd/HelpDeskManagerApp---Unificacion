"use client";

import { useEffect, useState } from "react";
import { slaApi } from "../api/sla-api";
import type { IncidenteVencido, SlaResumen } from "../types/sla";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import { StatsTable, type StatsColumn } from "@/shared/components/ui/stats-table";
import { Spinner } from "@/shared/components/ui/spinner";

function currentMonthValue(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

function monthValueToPeriodo(value: string): string {
  return value.replace("-", "");
}

function formatFecha(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

const incidenteColumns: StatsColumn<IncidenteVencido>[] = [
  {
    key: "id",
    label: "ID",
    className: "w-20",
    render: (row) => <span className="font-semibold tabular-nums">{row.id_incidente}</span>,
  },
  { key: "tecnico", label: "Técnico", render: (row) => row.tecnico },
  { key: "region", label: "Región", render: (row) => row.region },
  { key: "cliente", label: "Cliente", render: (row) => row.cliente },
  { key: "sucursal", label: "Sucursal", render: (row) => row.sucursal },
  { key: "modelo", label: "Modelo", render: (row) => row.modelo },
  {
    key: "fecha_operativo",
    label: "Operativo",
    render: (row) => (
      <span className="tabular-nums">{formatFecha(row.fecha_operativo)}</span>
    ),
  },
  { key: "rango", label: "Rango", render: (row) => row.rango },
  {
    key: "sla_horas",
    label: "SLA (h)",
    align: "right",
    className: "w-20",
    render: (row) => row.sla_horas,
  },
  {
    key: "horas_vencido",
    label: "Vencido (h)",
    align: "right",
    className: "w-28",
    render: (row) => (
      <span className="font-semibold text-[#dc2626] dark:text-[#f87171]">
        {row.horas_vencido}
      </span>
    ),
  },
];

export function SlaDetail() {
  const [monthValue, setMonthValue] = useState<string>(currentMonthValue());
  const [resumen, setResumen] = useState<SlaResumen | null>(null);
  const [incidentes, setIncidentes] = useState<IncidenteVencido[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Resetear datos al cambiar de período — "ajustar estado durante el render"
  // en vez de dentro del efecto (mismo patrón que confirmation-modal.tsx).
  const [prevMonthValue, setPrevMonthValue] = useState(monthValue);
  if (monthValue !== prevMonthValue) {
    setPrevMonthValue(monthValue);
    setLoading(true);
    setError(null);
    setResumen(null);
    setIncidentes([]);
  }

  useEffect(() => {
    let active = true;
    const periodo = monthValueToPeriodo(monthValue);
    Promise.all([slaApi.getResumen(periodo), slaApi.listIncidentesVencidos(periodo)])
      .then(([res, inc]) => {
        if (!active) return;
        setResumen(res);
        setIncidentes(inc);
      })
      .catch((err: unknown) => {
        if (!active) return;
        console.error("Error al cargar datos SLA:", err);
        setError(err instanceof Error ? err.message : "No se pudieron cargar los datos SLA.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [monthValue]);

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold text-foreground">SLA</h1>
          <p className="font-body text-sm text-muted-foreground">
            Cumplimiento de acuerdos de nivel de servicio por período.
          </p>
        </div>
        <label className="flex flex-col gap-1">
          <span className="font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
            Período
          </span>
          <input
            type="month"
            value={monthValue}
            onChange={(e) => setMonthValue(e.target.value)}
            className="rounded-[8px] border border-border bg-card px-3 py-1.5 font-body text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand-orange/60"
          />
        </label>
      </div>

      {loading && (
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      )}

      {!loading && error && (
        <p className="rounded-[12px] border border-destructive/40 bg-destructive/5 px-6 py-5 font-body text-sm text-foreground">
          {error}
        </p>
      )}

      {!loading && !error && resumen && (
        <div className="flex flex-col gap-6">
          <KpiGrid>
            <KpiTile
              label="Total de incidentes"
              value={resumen.total.toLocaleString("es-AR")}
              tone="neutral"
            />
            <KpiTile
              label="Correctos"
              value={resumen.correctos.toLocaleString("es-AR")}
              tone="orange"
              hint={`${resumen.pct_correctos.toLocaleString("es-AR", { maximumFractionDigits: 1 })}% del período`}
            />
            <KpiTile
              label="Vencidos"
              value={resumen.vencidos.toLocaleString("es-AR")}
              tone={resumen.vencidos > 0 ? "danger" : "neutral"}
              hint={`${resumen.pct_vencidos.toLocaleString("es-AR", { maximumFractionDigits: 1 })}% del período`}
            />
          </KpiGrid>

          <StatsTable
            title="Incidentes vencidos"
            subtitle={
              resumen.vencidos_por_tecnico.length > 0
                ? resumen.vencidos_por_tecnico
                    .map((t) => `${t.tecnico}: ${t.cantidad}`)
                    .join(" · ")
                : undefined
            }
            columns={incidenteColumns}
            rows={incidentes}
            rowKey={(row) => String(row.id_incidente)}
            emptyLabel="Sin incidentes vencidos en el período seleccionado."
          />
        </div>
      )}
    </div>
  );
}
