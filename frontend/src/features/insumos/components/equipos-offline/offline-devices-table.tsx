"use client";

import { Eye, EyeOff, Loader2 } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { SortableHeader, StatusBadge, type SortableColumn, type StatusTone } from "../shared";
import { formatArgDateTime } from "../../utils/format";
import type { SortState } from "../../hooks/use-table-sort";
import type { OfflineDeviceRow } from "../../types";
import type { OfflineSortKey } from "./offline-utils";

const COLUMNS: readonly SortableColumn<OfflineSortKey>[] = [
  { key: "model", label: "Modelo" },
  { key: "serial", label: "N° de serie" },
  { key: "customerName", label: "Cliente" },
  { key: "zone", label: "Zona" },
  { key: "lastContact", label: "Últ. contacto", className: "hidden lg:table-cell" },
  { key: "daysOffline", label: "Días offline", className: "hidden xl:table-cell" },
  { key: "cdStatus", label: "Veredicto CD" },
];

const CD_STATUS_TONE: Record<string, StatusTone> = {
  BODEGA: "advertencia",
  OTRO_CLIENTE: "activo",
  EN_CLIENTE: "ok",
  ERROR: "atencion",
};

function cdStatusLabel(cdStatus: string): string {
  switch (cdStatus) {
    case "BODEGA":
      return "Bodega";
    case "OTRO_CLIENTE":
      return "Otro cliente";
    case "EN_CLIENTE":
      return "En cliente";
    case "ERROR":
      return "Error";
    default:
      return "Sin verificar";
  }
}

interface OfflineDevicesTableProps {
  rows: readonly OfflineDeviceRow[];
  sort: SortState<OfflineSortKey>;
  onToggleSort: (key: OfflineSortKey) => void;
  canUpdate: boolean;
  canDelete: boolean;
  busyDeviceId: number | null;
  selected: ReadonlySet<number>;
  onToggleSelect: (deviceId: number) => void;
  onToggleDismissed: (device: OfflineDeviceRow, dismissed: boolean) => void;
}

export function OfflineDevicesTable({
  rows,
  sort,
  onToggleSort,
  canUpdate,
  canDelete,
  busyDeviceId,
  selected,
  onToggleSelect,
  onToggleDismissed,
}: OfflineDevicesTableProps) {
  const selectableRows = rows.filter((row) => row.deletable && !row.inMassOutage);
  const allSelected = selectableRows.length > 0 && selectableRows.every((r) => selected.has(r.deviceId));
  const someSelected = selectableRows.some((r) => selected.has(r.deviceId));

  function toggleAll() {
    if (allSelected) {
      selectableRows.forEach((r) => onToggleSelect(r.deviceId));
    } else {
      selectableRows
        .filter((r) => !selected.has(r.deviceId))
        .forEach((r) => onToggleSelect(r.deviceId));
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left font-body text-sm">
        <thead>
          <tr className="border-b border-border text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
            {canDelete && (
              <th scope="col" className="px-4 py-2">
                <input
                  type="checkbox"
                  checked={allSelected}
                  ref={(el) => {
                    if (el) el.indeterminate = someSelected && !allSelected;
                  }}
                  onChange={toggleAll}
                  aria-label="Seleccionar todos los eliminables"
                  className="cursor-pointer accent-brand-orange"
                  disabled={selectableRows.length === 0}
                />
              </th>
            )}
            {COLUMNS.map((column) => (
              <SortableHeader
                key={column.key}
                column={column}
                sort={sort}
                onToggleSort={onToggleSort}
                thClassName="px-4 py-2"
              />
            ))}
            <th scope="col" className="px-4 py-2 text-right">
              Acciones
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <OfflineRow
              key={row.deviceId}
              row={row}
              canUpdate={canUpdate}
              canDelete={canDelete}
              busy={busyDeviceId === row.deviceId}
              isSelected={selected.has(row.deviceId)}
              onToggleSelect={onToggleSelect}
              onToggleDismissed={onToggleDismissed}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function OfflineRow({
  row,
  canUpdate,
  canDelete,
  busy,
  isSelected,
  onToggleSelect,
  onToggleDismissed,
}: {
  row: OfflineDeviceRow;
  canUpdate: boolean;
  canDelete: boolean;
  busy: boolean;
  isSelected: boolean;
  onToggleSelect: (deviceId: number) => void;
  onToggleDismissed: (device: OfflineDeviceRow, dismissed: boolean) => void;
}) {
  const selectable = row.deletable && !row.inMassOutage;

  return (
    <tr
      className={cn(
        "border-b border-border last:border-0 transition-colors hover:bg-muted/30",
        row.offlineDismissed && "opacity-55",
        isSelected && "bg-brand-orange/5",
      )}
    >
      {canDelete && (
        <td className="px-4 py-2">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggleSelect(row.deviceId)}
            disabled={!selectable}
            aria-label={`Seleccionar ${row.serial}`}
            className={cn(
              "accent-brand-orange",
              selectable ? "cursor-pointer" : "cursor-not-allowed opacity-30",
            )}
          />
        </td>
      )}
      <td className="px-4 py-2 font-body text-sm text-foreground">{row.model || "—"}</td>
      <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{row.serial || "—"}</td>
      <td className="px-4 py-2 font-body text-sm text-foreground">{row.customerName || "—"}</td>
      <td className="px-4 py-2 font-body text-sm text-muted-foreground">{row.zone || "—"}</td>
      <td className="hidden whitespace-nowrap px-4 py-2 font-body text-sm text-muted-foreground lg:table-cell">
        {formatArgDateTime(row.lastContact)}
      </td>
      <td className="hidden whitespace-nowrap px-4 py-2 font-body text-sm text-muted-foreground xl:table-cell">
        {row.daysOffline != null ? `${row.daysOffline} d` : "—"}
      </td>
      <td className="px-4 py-2">
        <div className="flex flex-wrap items-center gap-1">
          <StatusBadge tone={CD_STATUS_TONE[row.cdStatus] ?? "neutral"}>
            {cdStatusLabel(row.cdStatus)}
          </StatusBadge>
          {row.offlineDismissed && <StatusBadge tone="neutral">Descartado</StatusBadge>}
          {row.inMassOutage && <StatusBadge tone="advertencia">Outage</StatusBadge>}
          {row.cdDetail && row.cdStatus !== "BODEGA" && (
            <span className="font-body text-xs text-muted-foreground" title={row.cdDetail}>
              {row.cdDetail.length > 32 ? `${row.cdDetail.slice(0, 32)}…` : row.cdDetail}
            </span>
          )}
        </div>
      </td>
      <td className="px-4 py-2">
        <div className="flex items-center justify-end">
          <button
            type="button"
            disabled={!canUpdate || busy}
            onClick={() => onToggleDismissed(row, !row.offlineDismissed)}
            title={
              canUpdate
                ? row.offlineDismissed
                  ? "Restaurar: vuelve a aparecer en la lista"
                  : "Descartar: no se da de baja, solo se oculta"
                : "Sin permiso para modificar equipos"
            }
            className="cursor-pointer rounded-[6px] p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:cursor-not-allowed disabled:pointer-events-none disabled:opacity-40"
          >
            {busy ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : row.offlineDismissed ? (
              <Eye className="h-3.5 w-3.5" />
            ) : (
              <EyeOff className="h-3.5 w-3.5" />
            )}
            <span className="sr-only">
              {row.offlineDismissed ? "Restaurar" : "Descartar"} {row.serial}
            </span>
          </button>
        </div>
      </td>
    </tr>
  );
}
