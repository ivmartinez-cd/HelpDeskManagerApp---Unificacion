"use client";

import { useCallback, useMemo, useState } from "react";
import { ConfirmationModal } from "../shared";
import type { AuditRow, DateRange } from "../../types";
import { EMPTY_VALUE, formatArgDateTime, formatNumber } from "../../utils/format";
import type { HistorialAuditState } from "../../hooks/use-historial-audit";
import { useHistorialAuditActions } from "../../hooks/use-historial-audit-actions";
import {
  EVENT_FILTER_ALL,
  eventLabel,
  isSystemEvent,
  matchesEventFilter,
  matchesRange,
  matchesSearch,
  rowAction,
} from "./audit-events";
import { AuditTable } from "./audit-table";
import { HistorialFilters } from "./historial-filters";
import { HistorialPagination } from "./historial-pagination";
import { LogDetailModal, type LogDetailField } from "./log-detail-modal";

/** Contenido de las tres pestañas que comparten la tabla de auditoría.
 *
 * Los filtros (pestaña, tipo de evento, rango, texto) y la paginación son
 * client-side sobre las filas ya traídas: `GET /api/insumos/audit` solo acepta
 * `page`/`size`. La ventana cargada crece con "Cargar más" y el total real del
 * envelope se muestra siempre, así que el operador ve sin ambigüedad sobre
 * cuánto historial está filtrando. */

const PAGE_SIZES = [25, 50, 100] as const;

interface AuditPanelProps {
  tab: "orders" | "system" | "all";
  audit: HistorialAuditState;
  search: string;
  onSearchChange: (value: string) => void;
  range: DateRange | null;
  onRangeChange: (range: DateRange | null) => void;
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
  tab,
  audit,
  search,
  onSearchChange,
  range,
  onRangeChange,
  canAct,
}: AuditPanelProps) {
  const [eventFilter, setEventFilter] = useState(EVENT_FILTER_ALL);
  const [size, setSize] = useState<number>(PAGE_SIZES[0]);
  const [page, setPage] = useState(1);
  const [detailRow, setDetailRow] = useState<AuditRow | null>(null);

  const actions = useHistorialAuditActions(audit.reload);

  // Volver a la página 1 cuando cambia cualquier filtro (ajuste de estado
  // durante el render, no un efecto).
  const filterKey = `${tab}/${eventFilter}/${search}/${range?.startDate ?? ""}-${range?.endDate ?? ""}/${size}`;
  const [prevFilterKey, setPrevFilterKey] = useState(filterKey);
  if (filterKey !== prevFilterKey) {
    setPrevFilterKey(filterKey);
    setPage(1);
  }

  const scoped = useMemo(() => {
    if (tab === "all") return audit.rows;
    if (tab === "system") return audit.rows.filter(isSystemEvent);
    return audit.rows.filter((row) => !isSystemEvent(row));
  }, [audit.rows, tab]);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return scoped.filter(
      (row) =>
        matchesEventFilter(row, eventFilter) &&
        matchesRange(row, range) &&
        matchesSearch(row, term),
    );
  }, [scoped, eventFilter, range, search]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / size));
  const safePage = Math.min(page, pageCount);
  const visible = filtered.slice((safePage - 1) * size, safePage * size);

  const actionFor = useCallback(
    (row: AuditRow) => rowAction(row, audit.rows),
    [audit.rows],
  );

  const pendingAction = actions.pending;

  return (
    <div className="flex flex-col gap-4">
      <HistorialFilters
        search={search}
        onSearchChange={onSearchChange}
        searchPlaceholder="Buscar cliente, serie, SKU, pedido…"
        eventFilter={eventFilter}
        onEventFilterChange={setEventFilter}
        range={range}
        onRangeChange={onRangeChange}
        summary={
          <>
            {formatNumber(filtered.length)} evento(s) filtrados sobre{" "}
            {formatNumber(audit.rows.length)} cargados de {formatNumber(audit.total)}
          </>
        }
      />

      <AuditTable
        rows={visible}
        actionFor={actionFor}
        canAct={canAct}
        busyRequestId={actions.busyRequestId}
        onCancel={(row) => actions.ask(row, "cancel")}
        onReconcile={(row) => actions.ask(row, "reconcile")}
        onDetail={setDetailRow}
        loading={audit.loading}
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <HistorialPagination
          page={safePage}
          pageCount={pageCount}
          from={filtered.length === 0 ? 0 : (safePage - 1) * size + 1}
          to={Math.min(safePage * size, filtered.length)}
          total={filtered.length}
          size={size}
          sizes={PAGE_SIZES}
          onPageChange={setPage}
          onSizeChange={setSize}
          noun="eventos"
        />
        {audit.hasMore && (
          <button
            type="button"
            onClick={() => void audit.loadMore()}
            disabled={audit.loadingMore}
            className="rounded-[8px] border border-border px-3.5 py-2 font-body text-xs font-bold text-foreground transition-colors hover:bg-muted disabled:pointer-events-none disabled:opacity-50"
          >
            {audit.loadingMore
              ? "Cargando…"
              : `Cargar más (faltan ${formatNumber(audit.total - audit.rows.length)})`}
          </button>
        )}
      </div>

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
