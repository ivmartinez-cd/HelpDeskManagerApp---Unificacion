"use client";

import { useMemo, useState } from "react";
import { ConfirmationModal } from "../shared";
import type { AuditRow, DateRange } from "../../types";
import { EMPTY_VALUE, formatArgDateTime, formatNumber } from "../../utils/format";
import { compareSortValues, useTableSort } from "../../hooks/use-table-sort";
import type { HistorialAuditState } from "../../hooks/use-historial-audit";
import { useHistorialAuditActions } from "../../hooks/use-historial-audit-actions";
import {
  AUDIT_DESC_FIRST,
  AUDIT_SORT_KEYS,
  AUDIT_SORT_STORAGE_KEY,
  auditSortValue,
  type AuditSortKey,
} from "./audit-sort";
import { eventLabel } from "./audit-events";
import { AuditTable } from "./audit-table";
import { HistorialFilters } from "./historial-filters";
import { HistorialPagination } from "./historial-pagination";
import { LogDetailModal, type LogDetailField } from "./log-detail-modal";

/** Contenido de las tres pestañas que comparten la tabla de auditoría.
 *
 * El filtrado (evento, rango, búsqueda, scope), la paginación y los
 * contadores de pestañas ya son responsabilidad de `HistorialView` +
 * `useHistorialAudit` (que le pega a `GET /api/insumos/audit` con todos esos
 * filtros como query params). Este componente solo:
 *  - ordena client-side las filas de la página YA traída (`audit-sort.ts`,
 *    el backend no soporta `order_by`);
 *  - controla el modal de detalle y las dos acciones condicionales
 *    (anular/vincular, vía `useHistorialAuditActions`).
 */

interface AuditPanelProps {
  audit: HistorialAuditState;
  eventFilter: string;
  onEventFilterChange: (value: string) => void;
  search: string;
  onSearchChange: (value: string) => void;
  range: DateRange | null;
  onRangeChange: (range: DateRange | null) => void;
  page: number;
  onPageChange: (page: number) => void;
  size: number;
  onSizeChange: (size: number) => void;
  sizes: readonly number[];
  /** El usuario puede anular/vincular (permiso `insumos:create`). */
  canAct: boolean;
}

function detailFields(row: AuditRow): LogDetailField[] {
  return [
    { label: "Evento", value: eventLabel(row) },
    { label: "Fecha de carga", value: formatArgDateTime(row.created_at) },
    { label: "Fecha de solicitud", value: formatArgDateTime(row.hp_request_time) },
    { label: "Cliente", value: row.customer_name ?? EMPTY_VALUE },
    { label: "Serie", value: row.device_serial ?? EMPTY_VALUE },
    { label: "SKU", value: row.sku ?? EMPTY_VALUE },
    { label: "Insumo", value: row.description ?? EMPTY_VALUE },
    { label: "Pedido CD", value: row.internal_order_id ?? EMPTY_VALUE },
    { label: "Solicitud HP", value: row.hp_request_id ? String(row.hp_request_id) : EMPTY_VALUE },
    { label: "Tipo", value: `${row.order_type}${row.dry_run ? " (simulación)" : ""}` },
  ];
}

export function AuditPanel({
  audit,
  eventFilter,
  onEventFilterChange,
  search,
  onSearchChange,
  range,
  onRangeChange,
  page,
  onPageChange,
  size,
  onSizeChange,
  sizes,
  canAct,
}: AuditPanelProps) {
  const [detailRow, setDetailRow] = useState<AuditRow | null>(null);

  const actions = useHistorialAuditActions(audit.reload);

  const { sort, toggleSort } = useTableSort<AuditSortKey>({
    initial: { key: "created_at", direction: "desc" }, // el orden actual del backend
    keys: AUDIT_SORT_KEYS,
    descFirstKeys: AUDIT_DESC_FIRST,
    storageKey: AUDIT_SORT_STORAGE_KEY,
  });

  // Orden client-side sobre la página que ya trajo el backend — no cambia
  // qué página se pide, solo cómo se muestra.
  const sortedRows = useMemo(
    () =>
      [...audit.rows].sort((a, b) =>
        compareSortValues(auditSortValue(a, sort.key), auditSortValue(b, sort.key), sort.direction),
      ),
    [audit.rows, sort],
  );

  const pageCount = Math.max(1, Math.ceil(audit.total / size));
  const from = audit.total === 0 ? 0 : (page - 1) * size + 1;
  const to = Math.min(page * size, audit.total);

  const pendingAction = actions.pending;

  return (
    <div className="flex flex-col gap-4">
      <HistorialFilters
        search={search}
        onSearchChange={onSearchChange}
        searchPlaceholder="Buscar cliente, serie, SKU, pedido…"
        eventFilter={eventFilter}
        onEventFilterChange={onEventFilterChange}
        range={range}
        onRangeChange={onRangeChange}
        summary={<>{formatNumber(audit.total)} evento(s)</>}
      />

      <AuditTable
        rows={sortedRows}
        canAct={canAct}
        busyRequestId={actions.busyRequestId}
        onCancel={(row) => actions.ask(row, "cancel")}
        onReconcile={(row) => actions.ask(row, "reconcile")}
        onDetail={setDetailRow}
        loading={audit.loading}
        sort={sort}
        onToggleSort={toggleSort}
      />

      <HistorialPagination
        page={page}
        pageCount={pageCount}
        from={from}
        to={to}
        total={audit.total}
        size={size}
        sizes={sizes}
        onPageChange={onPageChange}
        onSizeChange={onSizeChange}
        noun="eventos"
      />

      <LogDetailModal
        isOpen={detailRow !== null}
        title="Detalle del evento"
        fields={detailRow ? detailFields(detailRow) : []}
        output={detailRow?.detail}
        onClose={() => setDetailRow(null)}
      />

      <ConfirmationModal
        isOpen={pendingAction !== null}
        onClose={actions.dismiss}
        onConfirm={() => void actions.confirm()}
        title={pendingAction?.kind === "cancel" ? "Anular pedido" : "Vincular pedido"}
        variant={pendingAction?.kind === "cancel" ? "warning" : "simple"}
        confirmLabel={pendingAction?.kind === "cancel" ? "Anular pedido" : "Buscar y vincular"}
        loading={actions.running}
        error={actions.error}
      >
        {pendingAction?.kind === "cancel" ? (
          <>
            Se va a anular en Canal Directo el pedido{" "}
            <strong>{pendingAction.row.internal_order_id ?? pendingAction.row.hp_request_id}</strong>{" "}
            de la serie <strong>{pendingAction.row.device_serial ?? EMPTY_VALUE}</strong>. La
            solicitud vuelve a quedar pendiente y la acción no se puede deshacer.
          </>
        ) : (
          <>
            Busca en Canal Directo si el pedido de la solicitud{" "}
            <strong>{pendingAction?.row.hp_request_id}</strong> (serie{" "}
            <strong>{pendingAction?.row.device_serial ?? EMPTY_VALUE}</strong>) ya se había creado
            y lo vincula al historial. <strong>No crea ningún pedido nuevo.</strong>
          </>
        )}
      </ConfirmationModal>
    </div>
  );
}
