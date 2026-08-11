"use client";

import { ArrowDown, ArrowUp, ChevronsUpDown, ExternalLink, Eye, EyeOff, Loader2 } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { StatusBadge } from "../shared";
import { formatArgDateTime } from "../../utils/format";
import type { SortState } from "../../hooks/use-table-sort";
import type { NewDeviceRow } from "../../types";
import { toneForMonitorStatus, type NewDeviceSortKey } from "./new-devices-utils";

/** Tabla de Equipos Nuevos. No existe un componente de tabla ordenable
 * genérico en el proyecto, así que es `<table>` + Tailwind, con el estado de
 * orden inyectado desde afuera (`useTableSort`). */

interface Column {
  key: NewDeviceSortKey;
  label: string;
  /** Columnas que se esconden en pantallas chicas para que la tabla no
   * necesite scroll horizontal siempre. */
  className?: string;
}

const COLUMNS: readonly Column[] = [
  { key: "model", label: "Modelo" },
  { key: "serial", label: "N° de serie" },
  { key: "customerName", label: "Cliente" },
  { key: "zone", label: "Zona" },
  { key: "ipAddress", label: "IP", className: "hidden xl:table-cell" },
  { key: "discoveryDate", label: "Descubierto" },
  { key: "lastContact", label: "Últ. contacto", className: "hidden lg:table-cell" },
  { key: "monitorStatus", label: "Estado" },
];

interface NewDevicesTableProps {
  rows: readonly NewDeviceRow[];
  sort: SortState<NewDeviceSortKey>;
  onToggleSort: (key: NewDeviceSortKey) => void;
  canUpdate: boolean;
  busyDeviceId: number | null;
  onToggleDismissed: (device: NewDeviceRow, dismissed: boolean) => void;
}

export function NewDevicesTable({
  rows,
  sort,
  onToggleSort,
  canUpdate,
  busyDeviceId,
  onToggleDismissed,
}: NewDevicesTableProps) {
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full text-left font-body text-sm">
        <thead>
          <tr className="border-b border-border text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            {COLUMNS.map((column) => (
              <SortableHeader
                key={column.key}
                column={column}
                sort={sort}
                onToggleSort={onToggleSort}
              />
            ))}
            <th scope="col" className="px-4 py-3 text-right">
              Acciones
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.deviceId}
              className={cn(
                "border-b border-border last:border-0",
                row.dismissed && "opacity-55",
              )}
            >
              <td className="px-4 py-3 font-semibold text-foreground">{row.model || "—"}</td>
              <td className="px-4 py-3 font-mono text-xs text-foreground">{row.serial || "—"}</td>
              <td className="px-4 py-3 text-foreground">{row.customerName || "—"}</td>
              <td className="px-4 py-3 text-muted-foreground">{row.zone || "—"}</td>
              <td className="hidden px-4 py-3 font-mono text-xs text-muted-foreground xl:table-cell">
                {row.ipAddress || "—"}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                {formatArgDateTime(row.discoveryDate)}
              </td>
              <td className="hidden whitespace-nowrap px-4 py-3 text-muted-foreground lg:table-cell">
                {formatArgDateTime(row.lastContact)}
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap items-center gap-1.5">
                  <StatusBadge tone={toneForMonitorStatus(row.monitorStatus)}>
                    {row.monitorStatus || "Sin estado"}
                  </StatusBadge>
                  {row.dismissed && <StatusBadge tone="neutral">Ignorado</StatusBadge>}
                </div>
              </td>
              <td className="px-4 py-3">
                <RowActions
                  row={row}
                  canUpdate={canUpdate}
                  busy={busyDeviceId === row.deviceId}
                  onToggleDismissed={onToggleDismissed}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SortableHeader({
  column,
  sort,
  onToggleSort,
}: {
  column: Column;
  sort: SortState<NewDeviceSortKey>;
  onToggleSort: (key: NewDeviceSortKey) => void;
}) {
  const active = sort.key === column.key;
  const Icon = !active ? ChevronsUpDown : sort.direction === "asc" ? ArrowUp : ArrowDown;
  return (
    <th
      scope="col"
      aria-sort={active ? (sort.direction === "asc" ? "ascending" : "descending") : "none"}
      className={cn("px-4 py-3", column.className)}
    >
      <button
        type="button"
        onClick={() => onToggleSort(column.key)}
        className={cn(
          "inline-flex items-center gap-1 uppercase tracking-wide transition-colors hover:text-foreground",
          active && "text-brand-orange",
        )}
      >
        {column.label}
        <Icon className={cn("h-3 w-3", !active && "opacity-40")} aria-hidden="true" />
      </button>
    </th>
  );
}

function RowActions({
  row,
  canUpdate,
  busy,
  onToggleDismissed,
}: {
  row: NewDeviceRow;
  canUpdate: boolean;
  busy: boolean;
  onToggleDismissed: (device: NewDeviceRow, dismissed: boolean) => void;
}) {
  const iconButtonClass =
    "rounded-[8px] border border-border p-2 text-foreground transition-colors hover:bg-muted disabled:pointer-events-none disabled:opacity-40";
  return (
    <div className="flex items-center justify-end gap-1.5">
      {row.registrationUrl && (
        <a
          href={row.registrationUrl}
          target="_blank"
          rel="noopener noreferrer"
          title="Registrar en el portal de Insight"
          className={iconButtonClass}
        >
          <ExternalLink className="h-4 w-4" />
          <span className="sr-only">Registrar {row.serial}</span>
        </a>
      )}
      <button
        type="button"
        disabled={!canUpdate || busy}
        onClick={() => onToggleDismissed(row, !row.dismissed)}
        title={
          canUpdate
            ? row.dismissed
              ? "Restaurar: vuelve a contar como pendiente"
              : "Ignorar: no cuenta como pendiente"
            : "Sin permiso para modificar equipos"
        }
        className={iconButtonClass}
      >
        {busy ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : row.dismissed ? (
          <Eye className="h-4 w-4" />
        ) : (
          <EyeOff className="h-4 w-4" />
        )}
        <span className="sr-only">
          {row.dismissed ? "Restaurar" : "Ignorar"} {row.serial}
        </span>
      </button>
    </div>
  );
}
