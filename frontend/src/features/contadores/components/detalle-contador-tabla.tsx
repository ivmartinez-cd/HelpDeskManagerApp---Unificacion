"use client";

import { SortableHeader } from "@/shared/components/ui/sortable-header";
import type { SortState } from "@/shared/hooks/use-table-sort";
import { cn } from "@/shared/utils/cn";
import type { DetalleContadorRow } from "../types/detalle-contador-proceso";

/** Tabla del reporte "Detalle por Proceso" — extraída de
 * `DetalleContadorProcesoView` para no pasar el máximo de 300 líneas
 * (ARCHITECTURE_GUIDE.md §4). */

export type SortKey =
  | "empresa"
  | "sucursal"
  | "modelo"
  | "serie"
  | "sector"
  | "fecha_toma_anterior"
  | "contador_anterior"
  | "fecha_toma_actual"
  | "contador_actual"
  | "impresiones_reales"
  | "tipo"
  | "nombre_clase"
  | "estado_maquina"
  | "direccion_ip"
  | "mascara_ip";

export const SORT_KEYS: readonly SortKey[] = [
  "empresa",
  "sucursal",
  "modelo",
  "serie",
  "sector",
  "fecha_toma_anterior",
  "contador_anterior",
  "fecha_toma_actual",
  "contador_actual",
  "impresiones_reales",
  "tipo",
  "nombre_clase",
  "estado_maquina",
  "direccion_ip",
  "mascara_ip",
];

const numberFormat = new Intl.NumberFormat("es-AR");

function formatFecha(iso: string | null): string {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

/** Ancho de cada columna en % — `table-layout: fixed` (pedido explícito:
 * "que entre en el viewport sin generar scrollbar y se acomode según la
 * resolución de cada monitor"). Suman 100%, así el ancho real de cada
 * columna escala con el monitor en vez de un `min-width` fijo que
 * disparaba scroll horizontal en pantallas angostas. El contenido más
 * largo que su columna se trunca con "…" (`title` muestra el valor
 * completo al pasar el mouse). */
const ANCHOS_COL = [
  8, // Empresa
  9.4, // Sucursal
  9.4, // Modelo
  7.2, // Serie
  8, // Sector
  5.8, // Toma Ant.
  5.4, // Cont. Ant.
  5.8, // Toma Act.
  5.4, // Cont. Act.
  5.4, // Impr.
  8, // Tipo
  4, // Clase
  7.2, // Estado
  5.4, // Dir. IP
  5.4, // Másc. IP
] as const;

interface DetalleContadorTablaProps {
  filas: DetalleContadorRow[];
  sort: SortState<SortKey>;
  onToggleSort: (key: SortKey) => void;
}

export function DetalleContadorTabla({ filas, sort, onToggleSort }: DetalleContadorTablaProps) {
  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <table className="w-full table-fixed text-left text-sm">
        <colgroup>
          {ANCHOS_COL.map((ancho, i) => (
            <col key={i} style={{ width: `${ancho}%` }} />
          ))}
        </colgroup>
        <thead>
          <tr className="border-b border-border font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            <SortableHeader column={{ key: "empresa", label: "Empresa" }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5" />
            <SortableHeader column={{ key: "sucursal", label: "Sucursal" }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5" />
            <SortableHeader column={{ key: "modelo", label: "Modelo" }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5" />
            <SortableHeader column={{ key: "serie", label: "Serie" }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5" />
            <SortableHeader column={{ key: "sector", label: "Sector" }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5" />
            <SortableHeader column={{ key: "fecha_toma_anterior", label: "Toma Ant." }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5" />
            <SortableHeader column={{ key: "contador_anterior", label: "Cont. Ant." }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5 text-right" />
            <SortableHeader column={{ key: "fecha_toma_actual", label: "Toma Act." }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5" />
            <SortableHeader column={{ key: "contador_actual", label: "Cont. Act." }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5 text-right" />
            <SortableHeader column={{ key: "impresiones_reales", label: "Impr." }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5 text-right" />
            <SortableHeader column={{ key: "tipo", label: "Tipo" }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5" />
            <SortableHeader column={{ key: "nombre_clase", label: "Clase" }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5" />
            <SortableHeader column={{ key: "estado_maquina", label: "Estado" }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5" />
            <SortableHeader column={{ key: "direccion_ip", label: "Dir. IP" }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5" />
            <SortableHeader column={{ key: "mascara_ip", label: "Másc. IP" }} sort={sort} onToggleSort={onToggleSort} thClassName="truncate px-2.5 py-2.5" />
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {filas.length === 0 ? (
            <tr>
              <td colSpan={15} className="px-2.5 py-6 text-center text-muted-foreground">
                Sin filas para este alcance.
              </td>
            </tr>
          ) : (
            filas.map((fila, i) => (
              <tr key={`${fila.serie}-${fila.nombre_clase}-${i}`} className="hover:bg-muted/30">
                <td className="truncate px-2.5 py-2" title={fila.empresa}>
                  {fila.empresa}
                </td>
                <td className="truncate px-2.5 py-2" title={fila.sucursal}>
                  {fila.sucursal}
                </td>
                <td className="truncate px-2.5 py-2" title={fila.modelo}>
                  {fila.modelo}
                </td>
                <td className="truncate px-2.5 py-2 font-mono text-xs" title={fila.serie}>
                  {fila.serie}
                </td>
                <td className="truncate px-2.5 py-2" title={fila.sector ?? undefined}>
                  {fila.sector ?? "—"}
                </td>
                <td className="truncate px-2.5 py-2">{formatFecha(fila.fecha_toma_anterior)}</td>
                <td className="truncate px-2.5 py-2 text-right tabular-nums">
                  {numberFormat.format(fila.contador_anterior)}
                </td>
                <td className="truncate px-2.5 py-2">{formatFecha(fila.fecha_toma_actual)}</td>
                <td className="truncate px-2.5 py-2 text-right tabular-nums">
                  {numberFormat.format(fila.contador_actual)}
                </td>
                <td className="truncate px-2.5 py-2 text-right tabular-nums">
                  {numberFormat.format(fila.impresiones_reales)}
                </td>
                <td
                  className={cn("truncate px-2.5 py-2", fila.falta_contador && "font-bold text-destructive")}
                  title={fila.tipo ?? undefined}
                >
                  {fila.tipo ?? "—"}
                </td>
                <td className="truncate px-2.5 py-2">{fila.nombre_clase ?? "—"}</td>
                <td className="truncate px-2.5 py-2" title={fila.estado_maquina ?? undefined}>
                  {fila.estado_maquina ?? "—"}
                </td>
                <td className="truncate px-2.5 py-2" title={fila.direccion_ip ?? undefined}>
                  {fila.direccion_ip ?? "—"}
                </td>
                <td className="truncate px-2.5 py-2" title={fila.mascara_ip ?? undefined}>
                  {fila.mascara_ip ?? "—"}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
