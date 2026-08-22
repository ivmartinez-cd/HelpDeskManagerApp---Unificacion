"use client";

import { SortableHeader } from "@/shared/components/ui/sortable-header";
import type { SortState } from "@/shared/hooks/use-table-sort";
import { formatFecha, iniciales } from "../lib/fechas";
import type { Solicitud } from "../types/vacaciones";
import { SolicitudEstadoBadge } from "./solicitud-estado-badge";

export type SolicitudSortKey = "empleado" | "inicio" | "dias" | "estado";
export const SOLICITUD_SORT_KEYS: readonly SolicitudSortKey[] = ["empleado", "inicio", "dias", "estado"];

export function solicitudSortValue(s: Solicitud, key: SolicitudSortKey) {
  switch (key) {
    case "empleado": return s.empleadoNombre;
    case "inicio": return s.startDate;
    case "dias": return s.daysRequested;
    case "estado": return s.status;
  }
}

export function SolicitudesTabla({
  visibles,
  sort,
  onToggleSort,
  onEditar,
  onEliminar,
}: {
  visibles: Solicitud[];
  sort: SortState<SolicitudSortKey>;
  onToggleSort: (key: SolicitudSortKey) => void;
  onEditar: (s: Solicitud) => void;
  onEliminar: (s: Solicitud) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border">
      <table className="w-full min-w-[860px] font-body text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/30 text-left font-heading text-[11px] uppercase tracking-[.06em] text-muted-foreground">
            <SortableHeader column={{ key: "empleado", label: "Empleado" }} sort={sort} onToggleSort={onToggleSort} />
            <SortableHeader column={{ key: "inicio", label: "Rango" }} sort={sort} onToggleSort={onToggleSort} />
            <SortableHeader column={{ key: "dias", label: "Días" }} sort={sort} onToggleSort={onToggleSort} />
            <th className="px-4 py-3">Año cargo</th>
            <SortableHeader column={{ key: "estado", label: "Estado" }} sort={sort} onToggleSort={onToggleSort} />
            <th className="px-4 py-3">Motivo</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {visibles.map((s) => (
            <tr key={s.id} className="border-b border-border/60 last:border-0">
              <td className="px-4 py-3">
                <div className="flex items-center gap-2.5">
                  <span
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[8px] font-heading text-[11px] font-bold text-white"
                    style={{ backgroundColor: s.empleadoColor }}
                  >
                    {iniciales(s.empleadoNombre)}
                  </span>
                  <div>
                    <div className="font-semibold text-foreground">
                      {s.empleadoNombre}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {s.sectorNombre}
                    </div>
                  </div>
                </div>
              </td>
              <td className="px-4 py-3">
                <div className="text-foreground">{formatFecha(s.startDate)}</div>
                <div className="text-xs text-muted-foreground">
                  → {formatFecha(s.endDate)}
                </div>
              </td>
              <td className="px-4 py-3 text-right">
                <span className="font-semibold text-foreground">
                  {s.daysRequested}
                </span>{" "}
                <span className="text-xs text-muted-foreground">hábiles</span>
              </td>
              <td className="px-4 py-3 text-right text-muted-foreground">
                {s.chargedToYear ?? "—"}
              </td>
              <td className="px-4 py-3">
                <SolicitudEstadoBadge estado={s.status} />
              </td>
              <td className="max-w-[180px] truncate px-4 py-3 text-muted-foreground">
                {s.reason ?? "—"}
              </td>
              <td className="px-4 py-3 text-right">
                <div className="flex justify-end gap-1.5">
                  <button
                    type="button"
                    onClick={() => onEditar(s)}
                    className="rounded-[8px] border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-muted"
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    onClick={() => onEliminar(s)}
                    className="rounded-[8px] border border-destructive/40 px-3 py-1.5 text-xs font-semibold text-destructive hover:bg-destructive/10"
                  >
                    Eliminar
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
