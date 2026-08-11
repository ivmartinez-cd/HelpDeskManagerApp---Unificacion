"use client";

import { useMemo, type ReactNode } from "react";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { TonerBar, TrendChart, type TrendAnnotation } from "../shared";
import { useConsumableDetail } from "../../hooks/use-consumable-detail";
import type { ConsumableHistoryPoint, RequestRow } from "../../types";
import { EMPTY_VALUE, formatArgDateTime, formatPlainDate } from "../../utils/format";

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
 * 2. **Las ventanas "sin contacto" van como lista, no como franjas sobre el
 *    gráfico** — `TrendChart` es un primitivo compartido con Estadísticas y no
 *    soporta anotaciones de rango en X; agregarle esa capacidad tocaría código
 *    de otra pantalla. La información se muestra igual, debajo del gráfico.
 */

const TYPE_LABELS: Record<string, string> = {
  TONER: "Tóner",
  INK: "Tinta",
  DRUM: "Tambor",
  WASTE: "Residuos",
  FUSER: "Fusor",
  TRANSFER_UNIT: "Unidad de transferencia",
  MAINTENANCE_KIT: "Kit de mantenimiento",
};

const COLOUR_LABELS: Record<string, string> = {
  CYAN: "Cian",
  MAGENTA: "Magenta",
  YELLOW: "Amarillo",
  BLACK: "Negro",
  TRICOLOUR: "Tricolor",
  MULTICOLOUR: "Multicolor",
  NONE: "N/A",
  UNKNOWN: "Desconocido",
};

/** HP no publica un enum cerrado para `reason` (es texto libre): solo se
 * traduce lo visto en la práctica, el resto se muestra tal cual llega. */
const REASON_LABELS: Record<string, string> = { "LOW TONER": "Nivel bajo" };

function labelled(map: Record<string, string>, value: string | null | undefined): string {
  if (!value) return EMPTY_VALUE;
  return map[value] ?? value;
}

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h3 className="mb-2 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
      {children}
    </h3>
  );
}

interface InfoRow {
  term: string;
  detail: ReactNode;
}

function InfoList({ rows }: { rows: InfoRow[] }) {
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 font-body text-[12.5px]">
      {rows.map((row, index) => (
        <div key={`${row.term}-${index}`} className="contents">
          <dt className="whitespace-nowrap text-muted-foreground">{row.term}</dt>
          <dd className="break-words text-right text-foreground">{row.detail}</dd>
        </div>
      ))}
    </dl>
  );
}

function Note({ children }: { children: ReactNode }) {
  return <p className="font-body text-xs text-muted-foreground">{children}</p>;
}

/** Índice del punto del gráfico más cercano (hacia atrás) a una fecha dada. */
function indexForDate(points: ConsumableHistoryPoint[], iso: string | null | undefined): number {
  if (!iso || points.length === 0) return -1;
  const target = new Date(iso).getTime();
  if (Number.isNaN(target)) return -1;
  let index = 0;
  for (let i = 0; i < points.length; i += 1) {
    const pointTime = new Date(points[i].date).getTime();
    if (Number.isNaN(pointTime) || pointTime > target) break;
    index = i;
  }
  return index;
}

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
    <BrandModal isOpen onClose={onClose} title={row.description} widthPx={1080}>
      <div className="flex flex-col gap-5">
        <div className="flex flex-wrap items-center gap-4">
          <span className="font-mono text-[13px] text-muted-foreground">
            {row.serial} · {row.sku} · {row.store || EMPTY_VALUE}
          </span>
          <div className="min-w-[220px] flex-1">
            <TonerBar percent={row.percentLeft} size="lg" showValue />
          </div>
        </div>

        <div className="grid gap-5 lg:grid-cols-[minmax(240px,1fr)_minmax(320px,2fr)_minmax(200px,1fr)]">
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
                <p className="mt-2 font-body text-[11px] text-muted-foreground">
                  Punto rojo: solicitud actual · punto naranja: otras solicitudes del mismo
                  consumible.
                </p>
                {windows.length > 0 && (
                  <div className="mt-2 flex flex-col gap-1">
                    <p className="font-body text-[11px] font-bold text-muted-foreground">
                      Ventanas sin contacto del equipo
                    </p>
                    {windows.map((window) => (
                      <p
                        key={`${window.start}-${window.end}`}
                        className="font-body text-[11px] text-muted-foreground"
                      >
                        {formatArgDateTime(window.start)} → {formatArgDateTime(window.end)}
                      </p>
                    ))}
                  </div>
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
              <>
                <InfoList
                  rows={[
                    { term: "Lectura inicial", detail: formatArgDateTime(detail.data?.firstRead) },
                    { term: "Días monitoreado", detail: detail.data?.daysMonitored ?? EMPTY_VALUE },
                    {
                      term: "Ciclos monitoreados",
                      detail: detail.data?.engineCyclesMonitored ?? EMPTY_VALUE,
                    },
                  ]}
                />
                <p className="mt-2 font-body text-[11px] text-muted-foreground">
                  Nivel inicial y % utilizado no están disponibles fuera del portal HP.
                </p>
              </>
            )}
          </section>
        </div>

        <section>
          <SectionLabel>Historial de solicitudes (HP SDS)</SectionLabel>
          {consumableUnavailable || row.customerId === null || row.customerId === undefined ? (
            <Note>Sin datos suficientes para consultar el historial de solicitudes.</Note>
          ) : requests.loading ? (
            <Note>Cargando…</Note>
          ) : requests.error ? (
            <Note>{requests.error}</Note>
          ) : requests.data.length === 0 ? (
            <Note>Sin solicitudes registradas en Insight para este consumible.</Note>
          ) : (
            <div className="overflow-x-auto thin-scrollbar">
              <table className="w-full border-collapse font-body text-xs">
                <thead>
                  <tr className="border-b border-border text-left text-muted-foreground">
                    <th className="px-2 py-1.5 font-semibold">Fecha</th>
                    <th className="px-2 py-1.5 font-semibold">ID</th>
                    <th className="px-2 py-1.5 font-semibold">Motivo</th>
                    <th className="px-2 py-1.5 font-semibold">Nivel indicado</th>
                    <th className="px-2 py-1.5 font-semibold">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {requests.data.map((item) => (
                    <tr key={item.requestId} className="border-b border-border/50">
                      <td className="whitespace-nowrap px-2 py-1.5">
                        {formatArgDateTime(item.requested)}
                      </td>
                      <td className="px-2 py-1.5 font-mono">{item.requestId}</td>
                      <td className="px-2 py-1.5">{labelled(REASON_LABELS, item.reason)}</td>
                      <td className="px-2 py-1.5">
                        {item.requestedLevel !== null && item.requestedLevel !== undefined
                          ? `${item.requestedLevel}%`
                          : EMPTY_VALUE}
                      </td>
                      <td className="px-2 py-1.5">{item.statusLabel}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section>
          <SectionLabel>Pedidos recientes en Canal Directo</SectionLabel>
          {supplies.loading ? (
            <Note>Cargando…</Note>
          ) : supplies.error ? (
            <Note>{supplies.error}</Note>
          ) : supplies.data.length === 0 ? (
            <Note>Sin pedidos registrados para este equipo.</Note>
          ) : (
            <div className="overflow-x-auto thin-scrollbar">
              <table className="w-full border-collapse font-body text-xs">
                <thead>
                  <tr className="border-b border-border text-left text-muted-foreground">
                    <th className="px-2 py-1.5 font-semibold">Fecha</th>
                    <th className="px-2 py-1.5 font-semibold">SKU</th>
                    <th className="px-2 py-1.5 font-semibold">Descripción</th>
                    <th className="px-2 py-1.5 font-semibold">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {supplies.data.map((supply) => (
                    <tr key={supply.supply_id_full} className="border-b border-border/50">
                      <td className="whitespace-nowrap px-2 py-1.5">
                        {supply.fecha || EMPTY_VALUE}
                      </td>
                      <td className="px-2 py-1.5 font-mono">{supply.sku || EMPTY_VALUE}</td>
                      <td className="max-w-[20rem] truncate px-2 py-1.5" title={supply.descripcion}>
                        {supply.descripcion || EMPTY_VALUE}
                      </td>
                      <td className="px-2 py-1.5">
                        {supply.supplyUrl ? (
                          <a
                            href={supply.supplyUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-brand-orange underline underline-offset-2"
                          >
                            {supply.estado}
                          </a>
                        ) : (
                          supply.estado
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <div className="flex items-center justify-between gap-3 border-t border-border pt-4">
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
