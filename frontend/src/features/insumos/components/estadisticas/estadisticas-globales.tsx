"use client";

import { useMemo } from "react";
import Link from "next/link";
import { Spinner } from "@/shared/components/ui/spinner";
import { DateRangePickerPopover, TrendChart, type TrendAnnotation } from "../shared";
import {
  QUICK_PERIODS,
  rangeToQuery,
  useEstadisticasRange,
} from "../../hooks/use-estadisticas-range";
import { useEstadisticas } from "../../hooks/use-estadisticas";
import {
  EMPTY_VALUE,
  formatDayLabel,
  formatNumber,
  formatPlainDate,
} from "../../utils/format";
import { KpiGrid, KpiTile } from "./kpi-tile";
import { StatsTable, type StatsColumn } from "./stats-table";
import type { CustomerStat, EstadisticasResponse, SkuStat } from "../../types";

/** Estadísticas globales del módulo Insumos (`/insumos/estadisticas`).
 *
 * Todo lo que se muestra sale tal cual de `GET /api/insumos/estadisticas`: los
 * totales del período anterior ya vienen calculados del backend y el rango
 * efectivo también (`startDate`/`endDate` de la respuesta), así que la UI no
 * recalcula fechas por su cuenta.
 *
 * Diferencia con el legacy: el `TrendChart` compartido no dibuja bandas de
 * fondo (fines de semana). Los sábados y domingos se marcan en el subtítulo
 * del eje y no como franja; en cambio sí se anotan en rojo los días con
 * pedidos fallidos, que es el evento que el gráfico del legacy resaltaba.
 */

function rangeLabel(data: EstadisticasResponse): string {
  return `${formatPlainDate(data.startDate)} – ${formatPlainDate(data.endDate)}`;
}

function previousLabel(data: EstadisticasResponse): string {
  return `${formatPlainDate(data.previousStartDate)} – ${formatPlainDate(data.previousEndDate)}`;
}

export function EstadisticasGlobales() {
  const { range, filters, setRange, setLastDays } = useEstadisticasRange();
  const { data, loading, error } = useEstadisticas(filters);

  const labels = useMemo(() => (data?.series ?? []).map((p) => formatDayLabel(p.date)), [data]);
  const values = useMemo(() => (data?.series ?? []).map((p) => p.created), [data]);
  const annotations = useMemo<TrendAnnotation[]>(
    () =>
      (data?.series ?? []).flatMap((point, index) =>
        point.failed > 0
          ? [{ index, value: point.created, tone: "red" as const, label: "Fallidos" }]
          : [],
      ),
    [data],
  );

  const customerColumns: StatsColumn<CustomerStat>[] = [
    {
      key: "customer",
      label: "Cliente",
      render: (row) => (
        <Link
          href={`/insumos/estadisticas/clientes/${row.customerId}${rangeToQuery(range)}`}
          className="font-semibold text-brand-orange no-underline hover:underline"
        >
          {row.customerName}
        </Link>
      ),
    },
    { key: "created", label: "Creados", align: "right", render: (row) => formatNumber(row.created) },
    { key: "failed", label: "Fallidos", align: "right", render: (row) => formatNumber(row.failed) },
    { key: "total", label: "Total", align: "right", render: (row) => formatNumber(row.total) },
  ];

  const skuColumns: StatsColumn<SkuStat>[] = [
    { key: "sku", label: "SKU", render: (row) => <span className="font-semibold">{row.sku}</span> },
    {
      key: "description",
      label: "Descripción",
      render: (row) => (
        <span className="text-muted-foreground">{row.description || EMPTY_VALUE}</span>
      ),
    },
    { key: "count", label: "Pedidos", align: "right", render: (row) => formatNumber(row.count) },
  ];

  return (
    <div className="px-6 py-8 lg:px-9">
      <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-extrabold text-foreground">Estadísticas</h1>
          <p className="mt-1 font-body text-sm text-muted-foreground">
            {data
              ? `Pedidos de insumos entre ${rangeLabel(data)} (${data.days} días).`
              : "Tendencia de pedidos de insumos y rankings de clientes e insumos."}
          </p>
        </div>
        <DateRangePickerPopover
          value={range}
          onChange={setRange}
          minDate={data?.earliestDate ?? null}
          placeholder="Últimos 30 días"
        />
      </header>

      {loading && (
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      )}

      {!loading && error && (
        <p className="rounded-[12px] border border-destructive/40 bg-destructive/5 px-6 py-5 font-body text-sm text-foreground">
          No se pudieron cargar las estadísticas: {error}
        </p>
      )}

      {!loading && !error && data && (
        <div className="flex flex-col gap-6">
          <KpiGrid>
            <KpiTile
              label="Pedidos creados"
              value={formatNumber(data.totalCreated)}
              tone="orange"
              delta={{
                current: data.totalCreated,
                previous: data.previousCreated,
                periodLabel: previousLabel(data),
              }}
            />
            <KpiTile
              label="Pedidos fallidos"
              value={formatNumber(data.totalFailed)}
              tone={data.totalFailed > 0 ? "danger" : "neutral"}
              hint="Solicitudes que no se pudieron cargar en Canal Directo"
            />
            <KpiTile
              label="Promedio diario"
              value={data.dailyAverage.toLocaleString("es-AR", { maximumFractionDigits: 1 })}
              hint="Pedidos creados por día del período"
            />
            <KpiTile
              label="Día pico"
              value={data.peakDay ? formatPlainDate(data.peakDay) : EMPTY_VALUE}
              hint={
                data.peakDay ? `${formatNumber(data.peakDayCount)} pedidos ese día` : "Sin pedidos"
              }
            />
            <KpiTile
              label="Clientes activos"
              value={formatNumber(data.activeCustomers)}
              hint="Con al menos un pedido en el período"
            />
            <KpiTile
              label="Insumos distintos"
              value={formatNumber(data.distinctSkus)}
              hint="SKUs pedidos al menos una vez"
            />
          </KpiGrid>

          <TrendChart
            labels={labels}
            values={values}
            seriesLabel="Pedidos creados"
            annotations={annotations}
            title="Tendencia de pedidos"
            subtitle={`${rangeLabel(data)} · los puntos rojos marcan días con pedidos fallidos`}
            periods={QUICK_PERIODS}
            activePeriod={String(data.days)}
            onPeriodChange={(key) => setLastDays(Number(key))}
          />

          <div className="grid gap-6 xl:grid-cols-2">
            <StatsTable
              title="Clientes con más pedidos"
              subtitle="Top del período, ordenado por total"
              columns={customerColumns}
              rows={data.topCustomers}
              rowKey={(row) => String(row.customerId)}
            />
            <StatsTable
              title="Insumos más pedidos"
              subtitle="Top de SKUs del período"
              columns={skuColumns}
              rows={data.topSkus}
              rowKey={(row) => row.sku}
            />
          </div>
        </div>
      )}
    </div>
  );
}
