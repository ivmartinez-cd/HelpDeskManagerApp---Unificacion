"use client";

import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import { useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";
import { formatRango } from "../lib/fechas";
import type { Solicitud } from "../types/vacaciones";
import { ESTADO_SOLICITUD_LABEL, SolicitudEstadoBadge } from "./solicitud-estado-badge";

/** "Historial de decisiones" de Aprobaciones: una fila por solicitud con su
 * última decisión. Arranca en el orden del backend y ordena por cualquier
 * encabezado. */

type SortKey = "empleado" | "rango" | "dias" | "decision" | "decisor" | "comentario";

const COLUMNAS: SortableColumn<SortKey>[] = [
  { key: "empleado", label: "Empleado" },
  { key: "rango", label: "Rango" },
  { key: "dias", label: "Días", className: "text-right" },
  { key: "decision", label: "Decisión" },
  { key: "decisor", label: "Decisor" },
  { key: "comentario", label: "Comentario" },
];

const DESC_PRIMERO: readonly SortKey[] = ["rango", "dias"];

const decisionDe = (s: Solicitud) => (s.aprobaciones[0].decision === "APPROVED" ? "APPROVED" : "REJECTED");

function valorOrden(s: Solicitud, key: SortKey) {
  const ultima = s.aprobaciones[0];
  switch (key) {
    case "empleado": return s.empleadoNombre;
    case "rango": return s.startDate;
    case "dias": return s.daysRequested;
    case "decision": return ESTADO_SOLICITUD_LABEL[decisionDe(s)];
    case "decisor": return ultima.approverEmail;
    case "comentario": return ultima.comment;
  }
}

export function HistorialDecisionesTabla({ historial }: { historial: Solicitud[] }) {
  const { sort, toggleSort } = useOptionalTableSort(DESC_PRIMERO);
  const filas = useSortedRows(historial, sort, valorOrden);
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border">
      <table className="w-full min-w-[720px] font-body text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/30 text-left font-heading text-[11px] uppercase tracking-[.06em] text-muted-foreground">
            {COLUMNAS.map((c) => (
              <SortableHeader key={c.key} column={c} sort={sort} onToggleSort={toggleSort} />
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map((s) => {
            const ultima = s.aprobaciones[0];
            return (
              <tr key={s.id} className="border-b border-border/60 last:border-0">
                <td className="px-4 py-3 font-semibold text-foreground">{s.empleadoNombre}</td>
                <td className="px-4 py-3 text-muted-foreground">{formatRango(s.startDate, s.endDate)}</td>
                <td className="px-4 py-3 text-right text-foreground">{s.daysRequested}</td>
                <td className="px-4 py-3">
                  <SolicitudEstadoBadge estado={decisionDe(s)} />
                </td>
                <td className="px-4 py-3 text-muted-foreground">{ultima.approverEmail ?? "—"}</td>
                <td className="max-w-[220px] truncate px-4 py-3 text-muted-foreground">{ultima.comment ?? "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
