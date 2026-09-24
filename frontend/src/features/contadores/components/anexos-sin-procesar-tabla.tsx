"use client";

import { useCallback } from "react";
import type { AnexoSinProcesar } from "../types/calendario";
import { formatFecha } from "./equipos-sin-real-tabla";
import { formatPeriodo } from "./anexos-pendientes-tabla";
import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import { useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";

/** `operador_id` → nombre/color del catálogo local de operadores (ver
 * AnexosSinProcesarView, que lo resuelve una sola vez para toda la tabla). */
export interface OperadorInfo {
  nombre: string;
  color: string | null;
}

type SortKey =
  | "cliente"
  | "anexo"
  | "operador"
  | "fecha_evento"
  | "dias_vencido"
  | "periodo_esperado"
  | "ultimo_periodo_procesado";

const COLUMNAS: SortableColumn<SortKey>[] = [
  { key: "cliente", label: "Cliente" },
  { key: "anexo", label: "Anexo" },
  { key: "operador", label: "Operador" },
  { key: "fecha_evento", label: "Evento vencido desde" },
  { key: "dias_vencido", label: "Días vencido", className: "text-right" },
  { key: "periodo_esperado", label: "Se esperaba" },
  { key: "ultimo_periodo_procesado", label: "Último procesado" },
];

const DESC_PRIMERO: readonly SortKey[] = ["dias_vencido"];

export function AnexosSinProcesarTabla({
  rows,
  operadores,
}: {
  rows: AnexoSinProcesar[];
  operadores: Record<string, OperadorInfo>;
}) {
  const { sort, toggleSort } = useOptionalTableSort(DESC_PRIMERO);
  const valorOrden = useCallback(
    (a: AnexoSinProcesar, key: SortKey) =>
      key === "operador"
        ? a.operador_id && (operadores[a.operador_id]?.nombre ?? a.operador_id)
        : a[key],
    [operadores],
  );
  const filas = useSortedRows(rows, sort, valorOrden);
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full min-w-[980px] text-left">
        <thead>
          <tr className="border-b border-border font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            {COLUMNAS.map((column) => (
              <SortableHeader
                key={column.key}
                column={column}
                sort={sort}
                onToggleSort={toggleSort}
                thClassName="px-4 py-2.5"
              />
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {filas.map((a) => {
            const operador = a.operador_id ? operadores[a.operador_id] : undefined;
            return (
              <tr key={a.id_anexo} className="font-body text-sm hover:bg-muted/30">
                <td
                  className="max-w-[220px] truncate px-4 py-3 font-semibold text-foreground"
                  title={a.cliente}
                >
                  {a.cliente}
                </td>
                <td className="max-w-[220px] truncate px-4 py-3 text-foreground" title={a.anexo}>
                  {a.anexo}
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  {operador ? (
                    <span className="flex items-center gap-1.5">
                      <span
                        className="h-[7px] w-[7px] shrink-0 rounded-full"
                        style={{ background: operador.color ?? "#F7941D" }}
                      />
                      <span className="font-body text-sm text-foreground/80">
                        {operador.nombre}
                      </span>
                    </span>
                  ) : (
                    <span className="text-muted-foreground">{a.operador_id ?? "—"}</span>
                  )}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                  {formatFecha(a.fecha_evento)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right tabular-nums text-foreground">
                  {a.dias_vencido}
                </td>
                <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-muted-foreground">
                  {formatPeriodo(a.periodo_esperado)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-muted-foreground">
                  {a.ultimo_periodo_procesado ? formatPeriodo(a.ultimo_periodo_procesado) : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
