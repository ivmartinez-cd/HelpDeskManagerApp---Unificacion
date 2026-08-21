"use client";

import { Ban, Eye, Pencil } from "lucide-react";
import type { GrillaVariante } from "../../types/grilla-variantes";
import {
  ESTADO_VARIANTE_META,
  deriveEstadoVariante,
  formatFecha,
} from "../../lib/variante-estado";
import { BrandBadge } from "@/shared/components/ui/brand-form";

interface VariantesTablaProps {
  rows: GrillaVariante[];
  /** `turnos.manage` (ADR-029): sin esto solo se previsualiza. */
  canMutar?: boolean;
  onPreview: (variante: GrillaVariante) => void;
  onEdit: (variante: GrillaVariante) => void;
  onCancel: (variante: GrillaVariante) => void;
}

/** Listado de grillas de vacaciones: vigente + programadas + historial. Los
 * estados Programada/Vigente/Vencida se derivan por fecha en el cliente (la
 * DB solo persiste ACTIVA/CANCELADA, ADR-025). Solo las que siguen en juego
 * se editan/cancelan: una vencida o cancelada es registro histórico. */
export function VariantesTabla({
  rows,
  canMutar = true,
  onPreview,
  onEdit,
  onCancel,
}: VariantesTablaProps) {
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full min-w-[720px] text-left">
        <thead>
          <tr className="border-b border-border font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            <th className="px-4 py-2.5">Vigencia</th>
            <th className="px-4 py-2.5">Motivo</th>
            <th className="px-4 py-2.5">Franjas</th>
            <th className="px-4 py-2.5">Advertencias</th>
            <th className="px-4 py-2.5">Estado</th>
            <th className="px-4 py-2.5" />
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((v) => {
            const estado = deriveEstadoVariante(v);
            const meta = ESTADO_VARIANTE_META[estado];
            const mutable = canMutar && (estado === "vigente" || estado === "programada");
            const etiqueta = v.motivo ?? `grilla del ${formatFecha(v.desde)}`;
            const huecos = v.advertencias.filter((a) => a.tipo === "HUECO").length;
            return (
              <tr key={v.id} className="font-body text-sm">
                <td className="px-4 py-3 leading-tight text-foreground">
                  <p className="font-semibold">{formatFecha(v.desde)}</p>
                  <p className="text-muted-foreground">→ {formatFecha(v.hasta)}</p>
                </td>
                <td className="px-4 py-3 text-foreground">
                  <p>{v.motivo ?? "—"}</p>
                  {v.origenTexto && (
                    <p className="text-xs text-muted-foreground">{v.origenTexto}</p>
                  )}
                </td>
                <td className="px-4 py-3 text-muted-foreground">{v.slots.length}</td>
                <td className="px-4 py-3 text-muted-foreground">
                  {v.advertencias.length === 0 ? (
                    "—"
                  ) : (
                    <span title={`${huecos} hueco(s) de cobertura respecto de la grilla titular`}>
                      {v.advertencias.length}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <BrandBadge variant={meta.variant}>
                    <span aria-label={`Estado: ${meta.label}`}>{meta.label}</span>
                  </BrandBadge>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      type="button"
                      onClick={() => onPreview(v)}
                      aria-label={`Ver grilla ${etiqueta}`}
                      title="Ver cómo queda Turnos del día"
                      className="rounded-[8px] p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    {mutable && (
                      <button
                        type="button"
                        onClick={() => onEdit(v)}
                        aria-label={`Editar ${etiqueta}`}
                        title="Editar grilla"
                        className="rounded-[8px] p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                    )}
                    {mutable && (
                      <button
                        type="button"
                        onClick={() => onCancel(v)}
                        aria-label={`Cancelar ${etiqueta}`}
                        title="Cancelar grilla"
                        className="rounded-[8px] p-2 text-destructive transition-colors hover:bg-destructive/10"
                      >
                        <Ban className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
