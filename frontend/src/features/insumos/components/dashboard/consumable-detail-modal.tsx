"use client";

import { useMemo } from "react";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { TrendChart, tonerLevelColor, type TrendAnnotation } from "../shared";
import { useConsumableDetail } from "../../hooks/use-consumable-detail";
import type { RequestRow } from "../../types";
import { EMPTY_VALUE, formatArgDateTime, formatPlainDate } from "../../utils/format";
import {
  COLOUR_LABELS,
  ChartLegend,
  indexForDate,
  InfoList,
  labelled,
  Note,
  SectionLabel,
  StatBlock,
  TYPE_LABELS,
} from "./consumable-detail-primitives";
import { RequestsHistorySection, SuppliesSection } from "./consumable-detail-tables";

/** Detalle de un consumible: el componente más caro del legacy
 * (`ConsumableDetailModal.vue`, 799 líneas con ApexCharts).
 *
 * Dos diferencias deliberadas respecto del legacy:
 *
 * 1. **Chart.js en vez de ApexCharts** — el handoff pide Chart.js y el
 *    primitivo compartido `TrendChart` ya lo implementa. El truco del `:key`
 *    para forzar el remount (ApexCharts solo cableaba los `mouseEnter` de las
 *    anotaciones en el render inicial) no aplica igual acá, pero se conserva un
 *    `key` derivado del volumen de datos: es barato y garantiza que el chart se
 *    arme una sola vez, ya con las anotaciones async resueltas.
 * 2. **Las ventanas "sin contacto" van como texto, no como franjas sobre el
 *    gráfico** — `TrendChart` es un primitivo compartido con Estadísticas y no
 *    soporta anotaciones de rango en X; agregarle esa capacidad tocaría código
 *    de otra pantalla. La información se muestra igual, en una línea debajo
 *    del gráfico.
 */

interface ConsumableDetailModalProps {
  row: RequestRow | null;
  onClose: () => void;
}

export function ConsumableDetailModal({ row, onClose }: ConsumableDetailModalProps) {
  const { history, requests, detail, windows, supplies } = useConsumableDetail(row);

  const points = history.data;
  const labels = useMemo(() => points.map((point) => formatPlainDate(point.date)), [points]);
  const values = useMemo(() => points.map((point) => point.level ?? null), [points]);

  const annotations = useMemo<TrendAnnotation[]>(() => {
    if (points.length === 0 || !row) return [];
    const marks: TrendAnnotation[] = [];
    for (const item of requests.data) {
      if (item.requestId === row.requestId) continue;
      const index = indexForDate(points, item.requested);
      if (index < 0) continue;
      marks.push({
        index,
        value: points[index].level ?? item.requestedLevel ?? 0,
        tone: "orange",
        label: `Solicitud #${item.requestId} · ${item.statusLabel}`,
      });
    }
    const currentIndex = indexForDate(points, row.rawTime);
    if (currentIndex >= 0) {
      marks.push({
        index: currentIndex,
        value: points[currentIndex].level ?? row.percentLeft ?? 0,
        tone: "red",
        label: `Solicitud #${row.requestId} (actual)`,
      });
    }
    return marks;
  }, [points, requests.data, row]);

  if (!row) return null;

  const consumableUnavailable = row.consumableIndex === null || row.consumableIndex === undefined;

  return (
    <BrandModal isOpen onClose={onClose} title={row.description} widthPx={1400}>
      <div className="flex flex-col gap-4">
        <p className="-mt-2 font-mono text-[13px] text-muted-foreground">
          {row.serial} · <span className="text-brand-orange">{row.sku}</span>
        </p>

        <div className="grid gap-5 lg:grid-cols-[minmax(240px,1fr)_minmax(320px,2.4fr)_minmax(200px,1fr)]">
          <section>
            <SectionLabel>Detalle del consumible</SectionLabel>
            {consumableUnavailable ? (
              <Note>Insight no trajo el índice de este consumible en la última lectura.</Note>
            ) : detail.loading ? (
              <Note>Cargando…</Note>
            ) : detail.error ? (
              <Note>Sin datos ampliados en Insight ({detail.error}).</Note>
            ) : (
              <InfoList
                rows={[
                  { term: "Cliente", detail: row.customerName ?? EMPTY_VALUE },
                  { term: "Sucursal", detail: row.store || EMPTY_VALUE },
                  { term: "Modelo", detail: detail.data?.model || EMPTY_VALUE },
                  { term: "Tipo", detail: labelled(TYPE_LABELS, detail.data?.type) },
                  { term: "Color", detail: labelled(COLOUR_LABELS, detail.data?.colour) },
                  { term: "N° de serie", detail: detail.data?.serialNumber || "Desconocido" },
                  {
                    term: "SKU ajustado",
                    detail: <span className="font-mono">{detail.data?.sku || EMPTY_VALUE}</span>,
                  },
                  {
                    term: "Rendimiento ajustado",
                    detail: detail.data?.adjustedYield ?? "Desconocido",
                  },
                  {
                    term: "SKU del pedido",
                    detail: (
                      <span className="font-mono">{detail.data?.reorderSku || EMPTY_VALUE}</span>
                    ),
                  },
                  {
                    term: "Rendimiento del pedido",
                    detail: detail.data?.reorderYield ?? "Desconocido",
                  },
                  { term: "Capacidad", detail: detail.data?.capacity ?? EMPTY_VALUE },
                  {
                    term: "Nivel actual",
                    detail:
                      row.percentLeft !== null && row.percentLeft !== undefined ? (
                        <span style={{ color: tonerLevelColor(row.percentLeft) }}>
                          {Math.round(row.percentLeft)}%
                        </span>
                      ) : (
                        EMPTY_VALUE
                      ),
                  },
                  { term: "Días restantes", detail: row.daysLeft },
                  { term: "Páginas restantes", detail: row.pagesLeft ?? EMPTY_VALUE },
                  { term: "Última lectura", detail: formatArgDateTime(detail.data?.lastRead) },
                  { term: "Ciclos de trabajo", detail: detail.data?.engineCycles ?? EMPTY_VALUE },
                ]}
              />
            )}
          </section>

          <section>
            <SectionLabel>Historial de nivel</SectionLabel>
            {consumableUnavailable ? (
              <Note>Sin índice de consumible: no hay historial disponible.</Note>
            ) : history.loading ? (
              <Note>Cargando…</Note>
            ) : history.error ? (
              <Note>{history.error}</Note>
            ) : points.length === 0 ? (
              <Note>Sin lecturas históricas.</Note>
            ) : (
              <>
                <TrendChart
                  key={`${points.length}-${annotations.length}`}
                  labels={labels}
                  values={values}
                  seriesLabel="Nivel restante"
                  annotations={annotations}
                  heightPx={240}
                  formatValue={(value) => `${Math.round(value)}%`}
                  className="border-0 bg-transparent p-0"
                />
                <div className="mt-2">
                  <ChartLegend showNoContact={windows.length > 0} />
                </div>
                {windows.length > 0 && (
                  <p className="mt-1.5 font-body text-[11px] text-muted-foreground">
                    <span className="font-bold">Ventanas sin contacto del equipo:</span>{" "}
                    {windows
                      .map((window) => `${formatArgDateTime(window.start)} → ${formatArgDateTime(window.end)}`)
                      .join(" · ")}
                  </p>
                )}
              </>
            )}
          </section>

          <section>
            <SectionLabel>Detalles de rendimiento</SectionLabel>
            {consumableUnavailable || detail.error ? (
              <Note>{EMPTY_VALUE}</Note>
            ) : detail.loading ? (
              <Note>Cargando…</Note>
            ) : (
              <div className="flex flex-col gap-3">
                <StatBlock
                  label="Fecha de lectura inicial"
                  value={formatArgDateTime(detail.data?.firstRead)}
                />
                <StatBlock
                  label="Días en"
                  value={detail.data?.daysMonitored ?? EMPTY_VALUE}
                  size="large"
                />
                <StatBlock
                  label="Ciclos de trabajo en"
                  value={detail.data?.engineCyclesMonitored ?? EMPTY_VALUE}
                  size="large"
                />
                <p className="rounded-[10px] border border-border bg-muted/40 p-3 font-body text-[11px] text-muted-foreground">
                  Nivel inicial y % utilizado no están disponibles fuera del portal HP.
                </p>
              </div>
            )}
          </section>
        </div>

        <RequestsHistorySection
          row={row}
          requests={requests}
          consumableUnavailable={consumableUnavailable}
        />

        <SuppliesSection supplies={supplies} />

        <div className="flex items-center justify-between gap-3 border-t border-border pt-3">
          <a
            href={row.consumableUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="font-body text-sm font-semibold text-brand-orange underline underline-offset-2"
          >
            Ver equipo en Insight ↗
          </a>
          <button
            type="button"
            onClick={onClose}
            className={brandButtonClasses({ variant: "outline", className: "rounded-[8px]" })}
          >
            Cerrar
          </button>
        </div>
      </div>
    </BrandModal>
  );
}
