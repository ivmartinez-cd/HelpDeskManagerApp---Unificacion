"use client";

import { useMemo, useState } from "react";
import type { DateRange, MailLogRow } from "../../types";
import { formatArgDateTime, formatNumber } from "../../utils/format";
import type { HistorialMailLogState } from "../../hooks/use-historial-mail-log";
import { MAIL_LOG_PAGE_SIZES } from "../../hooks/use-historial-mail-log";
import { HistorialFilters } from "./historial-filters";
import { HistorialPagination } from "./historial-pagination";
import { LogDetailModal, type LogDetailField } from "./log-detail-modal";
import {
  MAIL_KIND_ALL,
  MAIL_KIND_OPTIONS,
  MailLogTable,
  mailKindLabel,
  matchesMailKind,
  matchesMailRange,
  matchesMailSearch,
} from "./mail-log-table";

/** Pestaña "Mails enviados". Acá la paginación SÍ es la del servidor
 * (`page`/`size` del envelope): ninguna fila necesita mirar otra página. La
 * búsqueda, el tipo y el rango filtran la página cargada — el endpoint no
 * acepta filtros. */

interface MailLogPanelProps {
  mailLog: HistorialMailLogState;
  search: string;
  onSearchChange: (value: string) => void;
  range: DateRange | null;
  onRangeChange: (range: DateRange | null) => void;
}

function detailFields(row: MailLogRow): LogDetailField[] {
  return [
    { label: "Tipo", value: mailKindLabel(row.kind) },
    { label: "Estado", value: row.success ? "Enviado" : "Error de envío" },
    { label: "Enviado el", value: formatArgDateTime(row.sent_at) },
    { label: "Destinatarios", value: row.recipients },
    { label: "Asunto", value: row.subject },
  ];
}

export function MailLogPanel({
  mailLog,
  search,
  onSearchChange,
  range,
  onRangeChange,
}: MailLogPanelProps) {
  const [kind, setKind] = useState(MAIL_KIND_ALL);
  const [detailRow, setDetailRow] = useState<MailLogRow | null>(null);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return mailLog.rows.filter(
      (row) =>
        matchesMailKind(row, kind) &&
        matchesMailRange(row, range) &&
        matchesMailSearch(row, term),
    );
  }, [mailLog.rows, kind, range, search]);

  const failedCount = filtered.filter((row) => !row.success).length;
  const pageCount = Math.max(1, Math.ceil(mailLog.total / mailLog.size));

  return (
    <div className="flex flex-col gap-4">
      <HistorialFilters
        search={search}
        onSearchChange={onSearchChange}
        searchPlaceholder="Buscar asunto, destinatario, tipo…"
        range={range}
        onRangeChange={onRangeChange}
        summary={
          failedCount > 0 ? (
            <span className="font-bold text-[#dc2626] dark:text-[#f87171]">
              {formatNumber(failedCount)} mail(s) con error de envío
            </span>
          ) : (
            <>{formatNumber(filtered.length)} mail(s) en esta página</>
          )
        }
      >
        <label className="flex items-center gap-2 font-body text-xs text-muted-foreground">
          <span className="whitespace-nowrap">Tipo</span>
          <select
            value={kind}
            onChange={(event) => setKind(event.target.value)}
            className="rounded-[8px] border border-border bg-card px-2.5 py-2 font-body text-[13px] text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
          >
            {MAIL_KIND_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </HistorialFilters>

      <MailLogTable rows={filtered} loading={mailLog.loading} onDetail={setDetailRow} />

      <HistorialPagination
        page={mailLog.page}
        pageCount={pageCount}
        from={mailLog.total === 0 ? 0 : (mailLog.page - 1) * mailLog.size + 1}
        to={Math.min(mailLog.page * mailLog.size, mailLog.total)}
        total={mailLog.total}
        size={mailLog.size}
        sizes={MAIL_LOG_PAGE_SIZES}
        onPageChange={mailLog.setPage}
        onSizeChange={mailLog.setSize}
        noun="mails"
      />

      <LogDetailModal
        isOpen={detailRow !== null}
        title="Detalle del envío"
        fields={detailRow ? detailFields(detailRow) : []}
        output={detailRow?.success ? "Envío exitoso, sin errores registrados." : detailRow?.error}
        outputLabel="Error del envío"
        onClose={() => setDetailRow(null)}
      />
    </div>
  );
}
