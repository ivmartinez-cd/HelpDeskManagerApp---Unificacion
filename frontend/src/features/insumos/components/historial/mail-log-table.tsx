"use client";

import { useMemo } from "react";
import { CheckCircle2, XCircle } from "lucide-react";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";
import type { DateRange, MailLogRow } from "../../types";
import { EMPTY_VALUE, formatArgDateTime, toArgDateKey } from "../../utils/format";
import { StatusBadge } from "../shared";

type MailSortKey = "tipo" | "enviado" | "estado";
const MAIL_SORT_KEYS: readonly MailSortKey[] = ["tipo", "enviado", "estado"];

/** Pestaña "Mails enviados": log de lo que la app mandó (o intentó mandar) —
 * backup diario, alertas de poller caído/recuperado y aviso de pedidos por
 * vencer. Sirve para saber de un vistazo si los envíos están funcionando.
 *
 * El endpoint solo pagina (`page`/`size`), así que la búsqueda, el tipo y el
 * rango de fechas filtran sobre la página cargada — ver `matchesMailSearch` y
 * compañía, que usa la vista antes de pasar las filas acá. */

const KIND_LABELS: Record<string, string> = {
  backup: "Backup diario",
  poller_alert: "Poller caído",
  poller_recovery: "Poller recuperado",
  pending_order_alert: "Pedidos por vencer",
};

export const MAIL_KIND_ALL = "ALL";

export const MAIL_KIND_OPTIONS: { value: string; label: string }[] = [
  { value: MAIL_KIND_ALL, label: "Todos los tipos" },
  ...Object.entries(KIND_LABELS).map(([value, label]) => ({ value, label })),
];

export function mailKindLabel(kind: string): string {
  return KIND_LABELS[kind] ?? kind;
}

export function matchesMailKind(row: MailLogRow, kind: string): boolean {
  return kind === MAIL_KIND_ALL || row.kind === kind;
}

export function matchesMailSearch(row: MailLogRow, term: string): boolean {
  if (!term) return true;
  return [row.subject, row.recipients, mailKindLabel(row.kind), row.error ?? ""].some((field) =>
    field.toLowerCase().includes(term),
  );
}

export function matchesMailRange(row: MailLogRow, range: DateRange | null): boolean {
  if (!range) return true;
  const date = new Date(row.sent_at);
  if (Number.isNaN(date.getTime())) return false;
  const key = toArgDateKey(date);
  return key >= range.startDate && key <= range.endDate;
}

const thClass =
  "whitespace-nowrap px-3 py-2.5 text-left font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground";
const tdClass = "px-3 py-2.5 font-body text-[13px] text-foreground";

interface MailLogTableProps {
  rows: MailLogRow[];
  loading: boolean;
  onDetail: (row: MailLogRow) => void;
}

export function MailLogTable({ rows, loading, onDetail }: MailLogTableProps) {
  const { sort, toggleSort } = useTableSort<MailSortKey>({
    initial: { key: "enviado", direction: "desc" },
    keys: MAIL_SORT_KEYS,
    descFirstKeys: ["enviado"],
  });

  const sorted = useMemo(() => {
    const getSv = (r: MailLogRow) => {
      switch (sort.key) {
        case "tipo": return mailKindLabel(r.kind);
        case "enviado": return r.sent_at;
        case "estado": return r.success ? 1 : 0;
      }
    };
    return [...rows].sort((a, b) => compareSortValues(getSv(a), getSv(b), sort.direction));
  }, [rows, sort]);

  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-border bg-muted/40">
            <SortableHeader column={{ key: "estado", label: "Estado" }} sort={sort} onToggleSort={toggleSort} thClassName={thClass} />
            <SortableHeader column={{ key: "tipo", label: "Tipo" }} sort={sort} onToggleSort={toggleSort} thClassName={thClass} />
            <th scope="col" className={thClass}>Asunto</th>
            <th scope="col" className={thClass}>Destinatarios</th>
            <SortableHeader column={{ key: "enviado", label: "Enviado el" }} sort={sort} onToggleSort={toggleSort} thClassName={thClass} />
            <th scope="col" className={thClass}>Detalle</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td
                colSpan={6}
                className="px-3 py-10 text-center font-body text-sm text-muted-foreground"
              >
                {loading ? "Cargando…" : "No hay mails que coincidan con los filtros."}
              </td>
            </tr>
          )}

          {sorted.map((row) => (
            <tr key={row.id} className="border-b border-border last:border-0 hover:bg-muted/30">
              <td className={tdClass}>
                <StatusBadge tone={row.success ? "ok" : "atencion"}>
                  <span className="inline-flex items-center gap-1">
                    {row.success ? (
                      <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
                    ) : (
                      <XCircle className="h-3 w-3" aria-hidden="true" />
                    )}
                    {row.success ? "Enviado" : "Error"}
                  </span>
                </StatusBadge>
              </td>
              <td className={`${tdClass} whitespace-nowrap`}>{mailKindLabel(row.kind)}</td>
              <td className={`${tdClass} max-w-[320px] truncate`} title={row.subject}>
                {row.subject}
              </td>
              <td
                className={`${tdClass} max-w-[240px] truncate text-muted-foreground`}
                title={row.recipients}
              >
                {row.recipients || EMPTY_VALUE}
              </td>
              <td className={`${tdClass} whitespace-nowrap text-muted-foreground`}>
                {formatArgDateTime(row.sent_at)}
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
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
