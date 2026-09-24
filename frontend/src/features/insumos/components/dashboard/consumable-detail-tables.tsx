"use client";

import { SortableHeader, StatusBadge, tonerLevelColor, type SortableColumn } from "../shared";
import type { ConsumableDetailState } from "../../hooks/use-consumable-detail";
import type { RequestRow } from "../../types";
import { EMPTY_VALUE, formatArgDateTime } from "../../utils/format";
import { labelled, Note, REASON_LABELS, SectionLabel } from "./consumable-detail-primitives";
import { useOptionalTableSort, useSortedRows } from "../../hooks/use-optional-table-sort";
import {
  REQUEST_HISTORY_DESC_FIRST,
  requestHistorySortValue,
  SUPPLY_DESC_FIRST,
  supplySortValue,
  type RequestHistorySortKey,
  type SupplySortKey,
} from "./consumable-detail-sort";
import { toneForRequestStatus, toneForSupplyStatus } from "./consumable-status-tones";

/** Las dos tablas inferiores del modal de detalle de consumible: historial de
 * solicitudes en HP SDS y pedidos recientes en Canal Directo. Todas las
 * columnas ordenan (criterios en `consumable-detail-sort.ts`). */

const HEAD_CELL = "px-2 py-1 font-semibold";

const REQUEST_COLUMNS: readonly SortableColumn<RequestHistorySortKey>[] = [
  { key: "requested", label: "Fecha" },
  { key: "requestId", label: "ID" },
  { key: "reason", label: "Motivo" },
  { key: "requestedLevel", label: "Nivel indicado" },
  { key: "status", label: "Estado" },
];

const SUPPLY_COLUMNS: readonly SortableColumn<SupplySortKey>[] = [
  { key: "fecha", label: "Fecha" },
  { key: "sku", label: "SKU" },
  { key: "descripcion", label: "Descripción" },
  { key: "estado", label: "Estado" },
];

export function RequestsHistorySection({
  row,
  requests,
  consumableUnavailable,
}: {
  row: RequestRow;
  requests: ConsumableDetailState["requests"];
  consumableUnavailable: boolean;
}) {
  const { sort, toggleSort } = useOptionalTableSort(REQUEST_HISTORY_DESC_FIRST);
  const sortedRequests = useSortedRows(requests.data, sort, requestHistorySortValue);
  return (
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
                {REQUEST_COLUMNS.map((column) => (
                  <SortableHeader
                    key={column.key}
                    column={column}
                    sort={sort}
                    onToggleSort={toggleSort}
                    thClassName={HEAD_CELL}
                    buttonClassName="normal-case tracking-normal"
                  />
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedRequests.map((item) => (
                <tr key={item.requestId} className="border-b border-border/50">
                  <td className="whitespace-nowrap px-2 py-1">
                    {formatArgDateTime(item.requested)}
                  </td>
                  <td className="px-2 py-1 font-mono">{item.requestId}</td>
                  <td className="px-2 py-1">{labelled(REASON_LABELS, item.reason)}</td>
                  <td
                    className="px-2 py-1 font-semibold"
                    style={
                      item.requestedLevel !== null && item.requestedLevel !== undefined
                        ? { color: tonerLevelColor(item.requestedLevel) }
                        : undefined
                    }
                  >
                    {item.requestedLevel !== null && item.requestedLevel !== undefined
                      ? `${item.requestedLevel}%`
                      : EMPTY_VALUE}
                  </td>
                  <td className="px-2 py-1">
                    <StatusBadge tone={toneForRequestStatus(item.status)}>
                      {item.statusLabel}
                    </StatusBadge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export function SuppliesSection({ supplies }: { supplies: ConsumableDetailState["supplies"] }) {
  const { sort, toggleSort } = useOptionalTableSort(SUPPLY_DESC_FIRST);
  const sortedSupplies = useSortedRows(supplies.data, sort, supplySortValue);
  return (
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
                {SUPPLY_COLUMNS.map((column) => (
                  <SortableHeader
                    key={column.key}
                    column={column}
                    sort={sort}
                    onToggleSort={toggleSort}
                    thClassName={HEAD_CELL}
                    buttonClassName="normal-case tracking-normal"
                  />
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedSupplies.map((supply) => (
                <tr key={supply.supply_id_full} className="border-b border-border/50">
                  <td className="whitespace-nowrap px-2 py-1">
                    {supply.fecha || EMPTY_VALUE}
                  </td>
                  <td className="px-2 py-1 font-mono">{supply.sku || EMPTY_VALUE}</td>
                  <td className="max-w-[20rem] truncate px-2 py-1" title={supply.descripcion}>
                    {supply.descripcion || EMPTY_VALUE}
                  </td>
                  <td className="px-2 py-1">
                    {supply.supplyUrl ? (
                      <a
                        href={supply.supplyUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="cursor-pointer underline-offset-2 hover:underline"
                      >
                        <StatusBadge tone={toneForSupplyStatus(supply.estado)}>
                          {supply.estado}
                        </StatusBadge>
                      </a>
                    ) : (
                      <StatusBadge tone={toneForSupplyStatus(supply.estado)}>
                        {supply.estado}
                      </StatusBadge>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
