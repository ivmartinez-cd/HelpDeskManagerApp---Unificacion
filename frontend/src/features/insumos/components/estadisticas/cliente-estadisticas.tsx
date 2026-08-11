"use client";

import { useMemo } from "react";
import Link from "next/link";
import { ArrowLeft, Printer } from "lucide-react";
import { Spinner } from "@/shared/components/ui/spinner";
import { DateRangePickerPopover, TrendChart, type TrendAnnotation } from "../shared";
import {
  QUICK_PERIODS,
  rangeToQuery,
  useEstadisticasRange,
} from "../../hooks/use-estadisticas-range";
import { useEstadisticasCliente } from "../../hooks/use-estadisticas";
import { formatDayLabel, formatPlainDate } from "../../utils/format";
import { ClientePrintFooter, ClientePrintHeader, ClientePrintStyles } from "./cliente-print";
import { KpisCliente } from "./cliente-kpis";
import { TablasCliente } from "./cliente-tablas";
import { TiemposCliente } from "./cliente-tiempos";

/** Detalle de estadísticas de un cliente
 * (`/insumos/estadisticas/clientes/[id]`).
 *
 * Es de solo lectura y no necesita permisos extra: quien puede entrar al módulo
 * puede verla, y "Imprimir reporte" es `window.print()` del navegador.
 *
 * El `id` de la ruta es el `customerId` numérico de HP SDS (el mismo de
 * `CustomerStat.customerId` del ranking global). Si viene basura en la URL se
 * corta antes de pegarle al backend.
 */
export function ClienteEstadisticas({ id }: { id: string }) {
  const customerId = /^\d+$/.test(id) ? Number(id) : null;
  const { range, filters, setRange, setLastDays } = useEstadisticasRange();
  const { data, loading, error } = useEstadisticasCliente(customerId, filters);

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

  const periodLabel = data ? `${formatPlainDate(data.startDate)} – ${formatPlainDate(data.endDate)}` : "";

  return (
    <div data-print-root className="px-6 py-8 lg:px-9">
      <ClientePrintStyles />

      <Link
        data-print-hide
        href={`/insumos/estadisticas${rangeToQuery(range)}`}
        className="mb-4 inline-flex items-center gap-1.5 font-body text-xs font-bold uppercase tracking-wide text-muted-foreground no-underline hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Estadísticas
      </Link>

      {data && (
        <ClientePrintHeader
          customerName={data.customerName}
          startDate={data.startDate}
          endDate={data.endDate}
        />
      )}

      <header data-print-hide className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-extrabold text-foreground">
            {data?.customerName ?? "Detalle de cliente"}
          </h1>
          <p className="mt-1 font-body text-sm text-muted-foreground">
            {data
              ? `Pedidos de insumos entre ${periodLabel} (${data.days} días).`
              : "Estadísticas de pedidos de insumos del cliente."}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <DateRangePickerPopover
            value={range}
            onChange={setRange}
            minDate={data?.earliestDate ?? null}
            placeholder="Últimos 30 días"
          />
          <button
            type="button"
            onClick={() => window.print()}
            disabled={!data}
            className="inline-flex items-center gap-2 rounded-[8px] border border-border bg-card px-3.5 py-2.5 font-body text-sm font-semibold text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Printer className="h-4 w-4 flex-none text-brand-orange" aria-hidden="true" />
            Imprimir reporte
          </button>
        </div>
      </header>

      {loading && (
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      )}

      {!loading && error && (
        <p className="rounded-[12px] border border-destructive/40 bg-destructive/5 px-6 py-5 font-body text-sm text-foreground">
          No se pudo cargar el detalle del cliente: {error}
        </p>
      )}

      {!loading && !error && data && (
        <div className="flex flex-col gap-6">
          <KpisCliente data={data} />

          <TiemposCliente
            fulfillment={data.fulfillment}
            pendingToDispatch={data.pendingToDispatch}
          />

          {/* El wrapper solo existe para el modo impresión: marca el gráfico
              como bloque que no se parte entre páginas. */}
          <div data-print-card>
            <TrendChart
              labels={labels}
              values={values}
              seriesLabel="Pedidos creados"
              annotations={annotations}
              title="Tendencia de pedidos"
              subtitle={`${periodLabel} · los puntos rojos marcan días con pedidos fallidos`}
              periods={QUICK_PERIODS}
              activePeriod={String(data.days)}
              onPeriodChange={(key) => setLastDays(Number(key))}
            />
          </div>

          <TablasCliente data={data} />

          <ClientePrintFooter />
        </div>
      )}
    </div>
  );
}
