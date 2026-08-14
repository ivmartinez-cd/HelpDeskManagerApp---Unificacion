"use client";

import type { AnexoPendiente, EstadoAnexoPendiente } from "../types/anexos-pendientes";
import { formatFecha } from "./equipos-sin-real-tabla";
import { BrandBadge } from "@/shared/components/ui/brand-form";

export const ESTADO_META: Record<
  EstadoAnexoPendiente,
  { label: string; variant: "warning" | "danger" }
> = {
  en_proceso: { label: "En proceso", variant: "warning" },
  demorado: { label: "Demorado", variant: "danger" },
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

export function AnexosPendientesTabla({ rows }: { rows: AnexoPendiente[] }) {
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full min-w-[960px] text-left">
        <thead>
          <tr className="border-b border-border font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            <th className="px-4 py-2.5">Período</th>
            <th className="px-4 py-2.5">Estado</th>
            <th className="px-4 py-2.5">Grupo</th>
            <th className="px-4 py-2.5">Anexo</th>
            <th className="px-4 py-2.5">Vendedor</th>
            <th className="px-4 py-2.5">Moneda</th>
            <th className="px-4 py-2.5">Últ. proceso</th>
            <th className="px-4 py-2.5 text-right">USD</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((a) => {
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
