"use client";

import type { AnexoPendiente, EstadoAnexoPendiente } from "../types/anexos-pendientes";
import { formatFecha } from "./equipos-sin-real-tabla";
import { BrandBadge } from "@/shared/components/ui/brand-form";
import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import { useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";

export const ESTADO_META: Record<
  EstadoAnexoPendiente,
  { label: string; variant: "warning" | "danger" | "accent" }
> = {
  en_proceso: { label: "En proceso", variant: "warning" },
  demorado: { label: "Demorado", variant: "danger" },
  mes_en_curso: { label: "Mes en curso", variant: "accent" },
};

const usdFormat = new Intl.NumberFormat("es-AR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/** `202607` → `07/2026`, el formato del selector del legacy. */
export function formatPeriodo(periodo: string): string {
  return `${periodo.slice(4)}/${periodo.slice(0, 4)}`;
}

export function formatImporteUsd(importe: string): string {
  return usdFormat.format(Number(importe));
}

type SortKey =
  | "periodo"
  | "estado"
  | "grupo"
  | "anexo"
  | "operador"
  | "vendedor"
  | "moneda"
  | "fecha_proceso"
  | "importe_usd";

const COLUMNAS: SortableColumn<SortKey>[] = [
  { key: "periodo", label: "Período" },
  { key: "estado", label: "Estado" },
  { key: "grupo", label: "Grupo" },
  { key: "anexo", label: "Anexo" },
  { key: "operador", label: "Operador" },
  { key: "vendedor", label: "Vendedor" },
  { key: "moneda", label: "Moneda" },
  { key: "fecha_proceso", label: "Últ. proceso" },
  { key: "importe_usd", label: "USD", className: "text-right" },
];

const DESC_PRIMERO: readonly SortKey[] = ["periodo", "fecha_proceso", "importe_usd"];

function valorOrden(a: AnexoPendiente, key: SortKey) {
  if (key === "estado") return ESTADO_META[a.estado].label;
  if (key === "operador") return a.operador_nombre;
  if (key === "importe_usd") return Number(a.importe_usd);
  return a[key];
}

export function AnexosPendientesTabla({ rows }: { rows: AnexoPendiente[] }) {
  const { sort, toggleSort } = useOptionalTableSort(DESC_PRIMERO);
  const filas = useSortedRows(rows, sort, valorOrden);
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full min-w-[1060px] text-left">
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
            const meta = ESTADO_META[a.estado];
            return (
              <tr key={a.id_anexo} className="font-body text-sm hover:bg-muted/30">
                <td className="px-4 py-3 font-mono text-xs font-semibold text-foreground">
                  {formatPeriodo(a.periodo)}
                </td>
                <td className="px-4 py-3">
                  <BrandBadge variant={meta.variant}>{meta.label}</BrandBadge>
                </td>
                <td
                  className="max-w-[200px] truncate px-4 py-3 font-semibold text-foreground"
                  title={a.grupo ?? undefined}
                >
                  {a.grupo ?? "—"}
                </td>
                <td className="max-w-[260px] px-4 py-3">
                  <p className="truncate text-foreground" title={a.anexo}>
                    {a.anexo}
                  </p>
                  {a.contrato && a.contrato !== a.anexo && (
                    <p className="truncate text-xs text-muted-foreground" title={a.contrato}>
                      {a.contrato}
                    </p>
                  )}
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  {a.operador_nombre ? (
                    <span className="flex items-center gap-1.5">
                      <span
                        className="h-[7px] w-[7px] shrink-0 rounded-full"
                        style={{ background: a.operador_color ?? "#F7941D" }}
                      />
                      <span className="font-body text-sm text-foreground/80">
                        {a.operador_nombre}
                      </span>
                    </span>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </td>
                <td
                  className="max-w-[160px] truncate px-4 py-3 text-muted-foreground"
                  title={a.vendedor ?? undefined}
                >
                  {a.vendedor ?? "—"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                  {a.moneda ?? "—"}
                  {a.moneda_facturacion && a.moneda_facturacion !== a.moneda && (
                    <span className="text-xs"> → {a.moneda_facturacion}</span>
                  )}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                  {formatFecha(a.fecha_proceso)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right tabular-nums text-foreground">
                  {formatImporteUsd(a.importe_usd)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
