"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import type { SortState } from "../../hooks/use-table-sort";
import type { OfflineDeviceRow } from "../../types";
import type { OfflineGroup, OfflineSortKey } from "./offline-utils";
import { OFFLINE_GROUP_META } from "./offline-utils";
import { OfflineDevicesTable } from "./offline-devices-table";

interface OfflineSectionProps {
  group: OfflineGroup;
  rows: OfflineDeviceRow[];
  sort: SortState<OfflineSortKey>;
  onToggleSort: (key: OfflineSortKey) => void;
  canUpdate: boolean;
  canDelete: boolean;
  busyDeviceId: number | null;
  selected: ReadonlySet<number>;
  onToggleSelect: (deviceId: number) => void;
  onToggleDismissed: (device: OfflineDeviceRow, dismissed: boolean) => void;
}

/** Una sección colapsable de EquiposOfflineView: un grupo de equipos con el
 * mismo veredicto de CD (o en el mismo outage). Arranca expandida u oculta
 * según `defaultExpanded` de la meta del grupo, pero el operario puede
 * cambiarla libremente. */
export function OfflineSection({
  group,
  rows,
  sort,
  onToggleSort,
  canUpdate,
  canDelete,
  busyDeviceId,
  selected,
  onToggleSelect,
  onToggleDismissed,
}: OfflineSectionProps) {
  const meta = OFFLINE_GROUP_META[group];
  const [open, setOpen] = useState(meta.defaultExpanded && rows.length > 0);

  const ChevronIcon = open ? ChevronDown : ChevronRight;

  const isOutageSection = group === "caida_colector";
  const isBodegaSection = group === "bodega";

  return (
    <div className="rounded-[12px] border border-border bg-card">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className={cn(
          "flex w-full cursor-pointer items-center gap-2.5 px-4 py-3 transition-colors hover:bg-muted/40",
          isOutageSection && "border-l-4 border-l-[#ef4444]",
          isBodegaSection && "border-l-4 border-l-[#eab308]",
        )}
        aria-expanded={open}
      >
        <ChevronIcon className="h-4 w-4 flex-none text-muted-foreground" aria-hidden="true" />
        <span className="font-heading text-sm font-bold text-foreground">{meta.label}</span>
        <span
          className={cn(
            "inline-flex h-5 min-w-[20px] items-center justify-center rounded-full px-1.5 font-body text-[11px] font-bold",
            isOutageSection
              ? "bg-[rgba(239,68,68,.15)] text-[#ef4444]"
              : isBodegaSection
                ? "bg-[rgba(234,179,8,.15)] text-[#ca9a04]"
                : "bg-brand-orange/15 text-brand-orange",
          )}
        >
          {rows.length}
        </span>
      </button>

      {open && rows.length > 0 && (
        <div className="border-t border-border">
          <OfflineDevicesTable
            rows={rows}
            sort={sort}
            onToggleSort={onToggleSort}
            canUpdate={canUpdate}
            canDelete={canDelete}
            busyDeviceId={busyDeviceId}
            selected={selected}
            onToggleSelect={onToggleSelect}
            onToggleDismissed={onToggleDismissed}
          />
        </div>
      )}

    </div>
  );
}
