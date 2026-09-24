"use client";

import type { ReactNode } from "react";
import { BrandSkeleton } from "@/shared/components/ui/brand-form";
import { PaginationBar } from "@/shared/components/ui/pagination-bar";
import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import type { SortState } from "@/shared/hooks/use-table-sort";
import { formatPlainDate } from "@/shared/utils/date-arg";
import { cn } from "@/shared/utils/cn";
import type { ColumnaOrdenDespachos, FilaDespacho } from "../../types/despachados";
import { ChipSemaforo, ConExtra, EstadoOcaCelda, LimiteCelda, TD, TH, claseFila } from "./despacho-celdas";
import { alTeclearFila } from "./despacho-celdas";

const COLUMNAS: SortableColumn<ColumnaOrdenDespachos>[] = [
  { key: "color", label: "Color" },
  { key: "guia", label: "Guía" },
  { key: "remito", label: "Remito" },
  { key: "cliente", label: "Cliente" },
  { key: "incidente", label: "Incidente" },
  { key: "estado", label: "Estado OCA" },
  { key: "sucursal", label: "Sucursal" },
  { key: "fecha_estado", label: "Fecha estado" },
  { key: "limite", label: "Límite / aviso" },
];
export const TAMANIOS_PAGINA = [25, 50, 100] as const;

interface Props {
  subtitulo: string;
  filtros: ReactNode;
  filas: FilaDespacho[];
  total: number;
  loading: boolean;
  page: number;
  size: number;
  onPage: (page: number) => void;
  onSize: (size: number) => void;
  /** Con `urgencia` (el defecto) ningún encabezado queda activo. */
  orden: SortState<ColumnaOrdenDespachos>;
  onOrdenar: (columna: ColumnaOrdenDespachos) => void;
  seleccionada: string | null;
  onAbrir: (guia: string) => void;
}

/** "Todos los despachos": filtros + tabla ordenada y paginada en el servidor.
 * Cada encabezado ordena por su columna (clic: asc; otro clic: desc). Las filas
 * son clickeables y accesibles por teclado (Enter/Espacio abren el panel). */
export function DespachosTable(props: Props) {
  const { filas, loading, seleccionada, onAbrir } = props;
  return (
    <section aria-labelledby="despachados-todos" className="rounded-[12px] border border-border bg-card">
      <div className="border-b border-border px-5 py-4">
        <h2 id="despachados-todos" className="font-heading text-base font-bold leading-6 text-foreground">
          Todos los despachos
        </h2>
        <p className="mt-0.5 font-body text-[13px] text-muted-foreground">{props.subtitulo}</p>
      </div>
      {props.filtros}
      <div className="overflow-x-auto" aria-busy={loading}>
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-muted/40">
              {COLUMNAS.map((c) => (
                <SortableHeader key={c.key} column={c} sort={props.orden} onToggleSort={props.onOrdenar} thClassName={TH} />
              ))}
            </tr>
          </thead>
          <tbody className={cn(loading && filas.length > 0 && "opacity-60")}>
            {loading && filas.length === 0 ? (
              <tr>
                <td colSpan={9} className="p-5"><BrandSkeleton className="h-40 w-full" /></td>
              </tr>
            ) : filas.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-5 py-9 text-center font-body text-[13px] text-muted-foreground">
                  <b className="mb-0.5 block text-foreground">Ningún despacho coincide con los filtros</b>
                  Probá con otra guía o cliente, o tocá &quot;Limpiar filtros&quot;.
                </td>
              </tr>
            ) : (
              filas.map((f) => (
                <tr
                  key={f.guia}
                  tabIndex={0}
                  className={claseFila(seleccionada === f.guia)}
                  onClick={() => onAbrir(f.guia)}
                  onKeyDown={(e) => alTeclearFila(e, () => onAbrir(f.guia))}
                >
                  <td className={TD}><ChipSemaforo color={f.color} estado={f.estado} observacion={f.observacion} /></td>
                  <td className={cn(TD, "whitespace-nowrap font-semibold tabular-nums tracking-[.01em]")}>{f.guia}</td>
                  <td className={cn(TD, "whitespace-nowrap tabular-nums")}>
                    <ConExtra valor={f.numeroRemito === null ? "" : String(f.numeroRemito)} cantidad={f.cantidadRemitos} />
                    <span className="block text-xs text-muted-foreground">{formatPlainDate(f.fechaRemito)}</span>
                  </td>
                  <td className={TD}>{f.cliente}</td>
                  <td className={cn(TD, "tabular-nums")}><ConExtra valor={f.incidente} cantidad={f.cantidadIncidentes} /></td>
                  <td className={TD}><EstadoOcaCelda fila={f} /></td>
                  <td className={TD}>{f.sucursalOca || "—"}</td>
                  <td className={cn(TD, "whitespace-nowrap tabular-nums")}>{formatPlainDate(f.fechaEstado)}</td>
                  <td className={TD}><LimiteCelda fila={f} /></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <PaginationBar
        className="border-t border-border px-5 py-3"
        page={props.page}
        total={props.total}
        size={props.size}
        onPageChange={props.onPage}
        noun="despachos"
        sizes={TAMANIOS_PAGINA}
        onSizeChange={props.onSize}
      />
    </section>
  );
}
