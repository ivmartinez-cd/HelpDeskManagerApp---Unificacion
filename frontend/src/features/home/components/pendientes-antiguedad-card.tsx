"use client";

import { BarElement, CategoryScale, Chart as ChartJS, LinearScale, Tooltip } from "chart.js";
import Link from "next/link";
import { Bar } from "react-chartjs-2";
import type { CalendarEvent, Operador } from "@/features/contadores/types/calendario";
import {
  cleanTitle,
  diasDeAtraso,
  formatDateLocal,
  textoAtraso,
} from "@/features/contadores/utils/calendario-format";
import { AGING_BUCKETS, agingDotColor } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

const TOP_LISTA = 6;

interface Pendiente {
  id: string;
  nombre: string;
  operador: string | null;
  dias: number;
}

function preparar(eventos: CalendarEvent[], operadores: Operador[]): Pendiente[] {
  const hoy = formatDateLocal(new Date());
  const porId = new Map(operadores.map((op) => [op.id, op.nombre]));
  return eventos
    .map((evt) => ({
      id: evt.id,
      nombre: evt.cliente || cleanTitle(evt.title) || "Sin nombre",
      operador: evt.operador_id ? (porId.get(evt.operador_id) ?? null) : null,
      dias: diasDeAtraso(evt.start, hoy),
    }))
    .sort((a, b) => b.dias - a.dias);
}

export function PendientesAntiguedadCard({
  eventos,
  operadores,
  loading,
  error,
}: {
  eventos: CalendarEvent[];
  operadores: Operador[];
  loading: boolean;
  error: string | null;
}) {
  const pendientes = preparar(eventos, operadores);
  const buckets = AGING_BUCKETS.map(
    (b) => pendientes.filter((p) => p.dias >= b.min && p.dias <= b.max).length,
  );

  return (
    <DashboardCard
      title="Pendientes por antigüedad"
      subtitle="Facturación sin cerrar · esperando contadores del cliente"
      loading={loading}
      error={error}
      headerRight={
        !loading && !error && pendientes.length > 0 ? (
          <span className="shrink-0 rounded-full bg-red-500/15 px-2.5 py-0.5 font-heading text-[12px] font-extrabold text-red-400">
            {pendientes.length}
          </span>
        ) : undefined
      }
    >
      {pendientes.length === 0 ? (
        <span className="pt-3 font-body text-[13px] text-muted-foreground">
          No hay facturación pendiente de días anteriores.
        </span>
      ) : (
        <>
          <div className="relative mt-2 h-[150px]">
            <Bar
              data={{
                labels: AGING_BUCKETS.map((b) => b.label),
                datasets: [
                  {
                    data: buckets,
                    backgroundColor: AGING_BUCKETS.map((b) => b.color),
                    borderRadius: 5,
                    barPercentage: 0.62,
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                  tooltip: {
                    callbacks: {
                      label: (c) => ` ${c.raw as number} ${(c.raw as number) === 1 ? "cliente" : "clientes"}`,
                    },
                  },
                },
                scales: {
                  x: {
                    grid: { display: false },
                    ticks: { color: "rgba(255,255,255,.4)", font: { size: 9.5 } },
                  },
                  y: {
                    grid: { color: "rgba(255,255,255,.06)" },
                    ticks: { color: "rgba(255,255,255,.4)", font: { size: 10 }, stepSize: 3 },
                  },
                },
              }}
            />
          </div>
          <div className="mt-3 flex flex-col gap-1.5 border-t border-border/60 pt-3">
            {pendientes.slice(0, TOP_LISTA).map((p) => (
              <div key={p.id} className="flex items-center gap-2">
                <span
                  className="h-[7px] w-[7px] shrink-0 rounded-full"
                  style={{ background: agingDotColor(p.dias) }}
                />
                <span className="flex-1 truncate font-body text-[12.5px] font-semibold text-foreground/75">
                  {p.nombre}
                  {p.operador && ` · ${p.operador}`}
                </span>
                <span
                  className="shrink-0 font-body text-[11px] font-semibold"
                  style={{ color: agingDotColor(p.dias) }}
                >
                  {textoAtraso(p.dias)}
                </span>
              </div>
            ))}
            <Link
              href="/contadores/calendario"
              className="mt-1 font-body text-[12.5px] font-bold text-brand-orange hover:text-brand-orange-hover"
            >
              Ver los {pendientes.length} pendientes →
            </Link>
          </div>
        </>
      )}
    </DashboardCard>
  );
}
