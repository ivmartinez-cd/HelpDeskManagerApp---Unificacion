"use client";

import type { ReactNode } from "react";
import type { DashboardModal } from "../../hooks/use-order-actions";
import type { RequestRow } from "../../types";
import { EMPTY_VALUE } from "../../utils/format";

/** Helpers y primitivos compartidos por los modales de conflicto del Dashboard
 * (`dashboard-modals.tsx`, `dashboard-conflict-modals.tsx`). */

export function value(data: Record<string, unknown> | null | undefined, key: string): string {
  const raw = data?.[key];
  if (raw === null || raw === undefined || raw === "") return EMPTY_VALUE;
  return String(raw);
}

export function stringOrNull(
  data: Record<string, unknown> | null | undefined,
  key: string,
): string | null {
  const raw = data?.[key];
  return typeof raw === "string" && raw.length > 0 ? raw : null;
}

/** Grilla `término / valor` de dos columnas, el mismo `<dl>` de los modales
 * del legacy. Las filas son objetos y no tuplas para no meter JSX suelto
 * dentro de un array literal (regla `react/jsx-key`). */
interface InfoRow {
  term: string;
  detail: ReactNode;
}

export function InfoGrid({ rows }: { rows: InfoRow[] }) {
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 font-body text-[13px]">
      {rows.map((row, index) => (
        <div key={`${row.term}-${index}`} className="contents">
          <dt className="whitespace-nowrap text-muted-foreground">{row.term}</dt>
          <dd className="break-all text-foreground">{row.detail}</dd>
        </div>
      ))}
    </dl>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h3 className="font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
      {children}
    </h3>
  );
}

export function RequestSummary({ row }: { row: RequestRow }) {
  return (
    <div className="flex flex-col gap-1.5">
      <SectionLabel>Solicitud</SectionLabel>
      <InfoGrid
        rows={[
          ...(row.customerName ? [{ term: "Cliente", detail: row.customerName }] : []),
          { term: "Serie", detail: <span className="font-mono">{row.serial}</span> },
          { term: "Consumible", detail: row.description },
          { term: "SKU", detail: <span className="font-mono">{row.sku}</span> },
        ]}
      />
    </div>
  );
}

export interface ModalProps {
  modal: DashboardModal;
  busy: boolean;
  onClose: () => void;
  onConfirm: (selectedInsumoId?: string) => void;
}
