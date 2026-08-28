"use client";

import { ExternalLink, Loader2 } from "lucide-react";
import { SortableHeader, StatusBadge } from "../shared";
import type { SortState } from "../../hooks/use-table-sort";
import type { AuditRow } from "../../types";
import { EMPTY_VALUE, formatArgDateTime } from "../../utils/format";
import { type AuditSortKey } from "./audit-sort";
import { eventLabel, eventTone, sdsDeviceUrl, type RowAction } from "./audit-events";

/** Tabla plana del historial de auditoría — la comparten las pestañas "Solo
 * Pedidos", "Acciones del Sistema" y "Todos los Registros" (mismas columnas
 * que el legacy; lo único que cambia entre pestañas es qué filas entran).
 *
 * La tabla no decide nada: recibe las filas ya filtradas (por el backend) y
 * ordenadas (client-side, ver `audit-panel.tsx`). La acción disponible por
 * fila (`row.action`) también la calcula el backend contra toda la tabla. */

/** Anchos fijos (colgroup, table-fixed) para que el navegador no estire las
 * columnas según el contenido más ancho y aparezca scroll horizontal. `event`
 * lleva el mayor ancho: "Ignorado permanente" es el label más largo, y sin
 * espacio se pintaba encima de la columna siguiente en vez de truncar. Suman
 * 100%. */
const COLUMNS: readonly { key: AuditSortKey | null; label: string; width: string }[] = [
  { key: "event", label: "Evento", width: "11%" },
  { key: "hp_request_time", label: "F. Solicitud", width: "7%" },
  { key: "created_at", label: "F. Carga", width: "7%" },
  { key: "customer_name", label: "Cliente", width: "10%" },
  { key: "device_serial", label: "Serie", width: "8%" },
  { key: "sku", label: "SKU", width: "7%" },
  { key: "description", label: "Insumo", width: "14%" },
  { key: "initial_percent_left", label: "% al cargar", width: "4%" },
  { key: "initial_days_left", label: "Días rest.", width: "4%" },
  { key: "initial_pages_left", label: "Págs. rest.", width: "4%" },
  { key: "internal_order_id", label: "Pedido CD", width: "7%" },
  { key: null, label: "Detalle", width: "8%" },
  { key: null, label: "Acción", width: "9%" },
];

const thClass =
  "px-3 py-2.5 text-left font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground";
const tdClass = "px-3 py-2.5 font-body text-[13px] text-foreground align-middle";
const numericClass = `${tdClass} text-right tabular-nums`;
const mutedClass = "font-body text-[12px] text-muted-foreground";

interface AuditTableProps {
  rows: AuditRow[];
  /** El usuario tiene permiso para anular/vincular. */
  canAct: boolean;
  /** `hp_request_id` de la fila con una acción en vuelo. */
  busyRequestId: number | null;
  onCancel: (row: AuditRow) => void;
  onReconcile: (row: AuditRow) => void;
  onDetail: (row: AuditRow) => void;
  loading: boolean;
  sort: SortState<AuditSortKey>;
  onToggleSort: (key: AuditSortKey) => void;
}

export function AuditTable({
  rows,
  canAct,
  busyRequestId,
  onCancel,
  onReconcile,
  onDetail,
  loading,
  sort,
  onToggleSort,
}: AuditTableProps) {
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full table-fixed border-collapse">
        <colgroup>
          {COLUMNS.map((column) => (
            <col key={column.label} style={{ width: column.width }} />
          ))}
        </colgroup>
        <thead>
          <tr className="border-b border-border bg-muted/40">
            {COLUMNS.map((column) =>
              column.key !== null ? (
                <SortableHeader
                  key={column.key}
                  column={{ key: column.key, label: column.label }}
                  sort={sort}
                  onToggleSort={onToggleSort}
                  thClassName={thClass}
                />
              ) : (
                <th key={column.label} scope="col" className={thClass}>
                  {column.label}
                </th>
              ),
            )}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td
                colSpan={COLUMNS.length}
                className="px-3 py-10 text-center font-body text-sm text-muted-foreground"
              >
                {loading ? "Cargando…" : "No se encontraron eventos con los filtros seleccionados."}
              </td>
            </tr>
          )}

          {rows.map((row) => {
            const action: RowAction = row.action ?? null;
            const busy = busyRequestId !== null && busyRequestId === row.hp_request_id;
            const deviceUrl = sdsDeviceUrl(row.device_id);
            return (
              <tr key={row.id} className="border-b border-border last:border-0 hover:bg-muted/30">
                <td className={tdClass}>
                  <StatusBadge tone={eventTone(row)}>{eventLabel(row)}</StatusBadge>
                </td>
                <td className={`${tdClass} ${mutedClass}`}>
                  {formatArgDateTime(row.hp_request_time)}
                </td>
                <td className={`${tdClass} ${mutedClass}`}>
                  {formatArgDateTime(row.created_at)}
                </td>
                <td className={`${tdClass} break-words`} title={row.customer_name ?? ""}>
                  {row.customer_name ?? EMPTY_VALUE}
                </td>
                <td className={`${tdClass} truncate font-mono text-[12px]`} title={row.device_serial ?? ""}>
                  {row.device_serial && deviceUrl ? (
                    <a
                      href={deviceUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-brand-orange hover:underline"
                    >
                      {row.device_serial}
                      <ExternalLink className="h-3 w-3" aria-hidden="true" />
                    </a>
                  ) : (
                    (row.device_serial ?? EMPTY_VALUE)
                  )}
                </td>
                <td className={`${tdClass} truncate font-mono text-[12px]`} title={row.sku ?? ""}>
                  {row.sku ?? EMPTY_VALUE}
                </td>
                <td className={`${tdClass} truncate`} title={row.description ?? ""}>
                  {row.description ?? EMPTY_VALUE}
                </td>
                <td className={numericClass}>
                  {row.initial_percent_left != null ? `${row.initial_percent_left}%` : EMPTY_VALUE}
                </td>
                <td className={numericClass}>{row.initial_days_left ?? EMPTY_VALUE}</td>
                <td className={numericClass}>{row.initial_pages_left ?? EMPTY_VALUE}</td>
                <td
                  className={`${tdClass} truncate font-mono text-[12px]`}
                  title={row.internal_order_id ?? ""}
                >
                  {row.internal_order_id && row.supply_url ? (
                    <a
                      href={row.supply_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand-orange hover:underline"
                    >
                      {row.internal_order_id}
                    </a>
                  ) : (
                    (row.internal_order_id ?? EMPTY_VALUE)
                  )}
                </td>
                <td className={tdClass}>
                  <button
                    type="button"
                    onClick={() => onDetail(row)}
                    className="cursor-pointer rounded-[8px] border border-border px-2.5 py-1 font-body text-[12px] font-semibold text-foreground transition-colors hover:bg-muted"
                  >
                    Detalles
                  </button>
                </td>
                <td className={tdClass}>
                  <RowActionCell
                    action={canAct ? action : null}
                    busy={busy}
                    onCancel={() => onCancel(row)}
                    onReconcile={() => onReconcile(row)}
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

interface RowActionCellProps {
  action: RowAction;
  busy: boolean;
  onCancel: () => void;
  onReconcile: () => void;
}

function RowActionCell({ action, busy, onCancel, onReconcile }: RowActionCellProps) {
  if (action === null) return <span className={mutedClass}>{EMPTY_VALUE}</span>;

  const isCancel = action === "cancel";
  return (
    <button
      type="button"
      disabled={busy}
      onClick={isCancel ? onCancel : onReconcile}
      title={
        isCancel
          ? "Anula el pedido en Canal Directo y libera la solicitud"
          : "Busca si el pedido ya se creó en Canal Directo y lo vincula, sin crear uno nuevo"
      }
      className={
        isCancel
          ? "inline-flex cursor-pointer items-center gap-1.5 whitespace-nowrap rounded-[8px] bg-[#eab308] px-2.5 py-1 font-body text-[12px] font-bold text-white transition-colors hover:bg-[#ca9a04] disabled:cursor-not-allowed disabled:pointer-events-none disabled:opacity-50"
          : "inline-flex cursor-pointer items-center gap-1.5 whitespace-nowrap rounded-[8px] border border-border px-2.5 py-1 font-body text-[12px] font-semibold text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:pointer-events-none disabled:opacity-50"
      }
    >
      {busy && <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />}
      {isCancel ? (busy ? "Anulando…" : "Anular") : busy ? "Buscando…" : "Vincular"}
    </button>
  );
}
