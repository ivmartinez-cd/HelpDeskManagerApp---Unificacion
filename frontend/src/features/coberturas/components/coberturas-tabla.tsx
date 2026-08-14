"use client";

import { useMemo } from "react";
import { Ban, Pencil } from "lucide-react";
import type { Cobertura, CoberturaOperadorOption } from "../types/coberturas";
import { deriveEstado, ESTADO_META, formatFechaCorta } from "../lib/estado";
import { BrandBadge } from "@/shared/components/ui/brand-form";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { UserAvatar } from "@/shared/components/ui/user-avatar";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";

type CoberturasSortKey = "ausente" | "reemplazante" | "desde" | "estado";
const COBERTURAS_SORT_KEYS: readonly CoberturasSortKey[] = [
  "ausente", "reemplazante", "desde", "estado",
];

interface CoberturasTablaProps {
  rows: Cobertura[];
  operadorMeta: Map<string, CoberturaOperadorOption>;
  alcanceLabelOf: (id: string) => string;
  alcanceUnidad: string;
  canEdit: boolean;
  canCancel: boolean;
  onEdit: (cobertura: Cobertura) => void;
  onCancel: (cobertura: Cobertura) => void;
}

function OperadorCell({
  id,
  nombre,
  meta,
}: {
  id: string;
  nombre: string | null;
  meta: CoberturaOperadorOption | undefined;
}) {
  const display = nombre ?? meta?.nombre ?? id;
  return (
    <div className="flex items-center gap-2.5">
      <UserAvatar fullName={display} color={meta?.color ?? null} size="sm" />
      <div className="min-w-0 leading-tight">
        <p className="truncate font-body text-sm font-semibold text-foreground">{display}</p>
        {meta?.sublabel && (
          <p className="truncate font-body text-xs text-muted-foreground">{meta.sublabel}</p>
        )}
      </div>
    </div>
  );
}

export function CoberturasTabla({
  rows,
  operadorMeta,
  alcanceLabelOf,
  alcanceUnidad,
  canEdit,
  canCancel,
  onEdit,
  onCancel,
}: CoberturasTablaProps) {
  const { sort, toggleSort } = useTableSort<CoberturasSortKey>({
    initial: { key: "desde", direction: "desc" },
    keys: COBERTURAS_SORT_KEYS,
    descFirstKeys: ["desde"],
  });

  const sorted = useMemo(() => {
    const getSv = (c: Cobertura) => {
      switch (sort.key) {
        case "ausente": return c.ausenteNombre ?? c.ausenteId;
        case "reemplazante": return c.reemplazanteNombre ?? c.reemplazanteId;
        case "desde": return c.desde;
        case "estado": return deriveEstado(c);
      }
    };
    return [...rows].sort((a, b) => compareSortValues(getSv(a), getSv(b), sort.direction));
  }, [rows, sort]);

  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full min-w-[760px] text-left">
        <thead>
          <tr className="border-b border-border font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            <SortableHeader column={{ key: "ausente", label: "Ausente" }} sort={sort} onToggleSort={toggleSort} thClassName="px-4 py-2.5" />
            <SortableHeader column={{ key: "reemplazante", label: "Reemplazante" }} sort={sort} onToggleSort={toggleSort} thClassName="px-4 py-2.5" />
            <SortableHeader column={{ key: "desde", label: "Vigencia" }} sort={sort} onToggleSort={toggleSort} thClassName="px-4 py-2.5" />
            <th className="px-4 py-2.5">Alcance</th>
            <th className="px-4 py-2.5">Motivo</th>
            <SortableHeader column={{ key: "estado", label: "Estado" }} sort={sort} onToggleSort={toggleSort} thClassName="px-4 py-2.5" />
            <th className="px-4 py-2.5" />
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {sorted.map((c) => {
            const estado = deriveEstado(c);
            const meta = ESTADO_META[estado];
            // Solo las reglas aún en juego se pueden editar/cancelar: una
            // vencida o cancelada es un registro histórico (ADR-013).
            const mutable = estado === "activa" || estado === "programada";
            const editable = canEdit && mutable;
            const cancelable = canCancel && mutable;
            const alcanceLabels = c.alcanceItems.map(alcanceLabelOf);
            return (
              <tr key={c.id} className="font-body text-sm">
                <td className="px-4 py-3">
                  <OperadorCell
                    id={c.ausenteId}
                    nombre={c.ausenteNombre}
                    meta={operadorMeta.get(c.ausenteId)}
                  />
                </td>
                <td className="px-4 py-3">
                  <OperadorCell
                    id={c.reemplazanteId}
                    nombre={c.reemplazanteNombre}
                    meta={operadorMeta.get(c.reemplazanteId)}
                  />
                </td>
                <td className="px-4 py-3 leading-tight text-muted-foreground">
                  <p>{formatFechaCorta(c.desde)}</p>
                  <p>→ {formatFechaCorta(c.hasta)}</p>
                </td>
                <td className="px-4 py-3 text-muted-foreground">
                  {c.alcanceTotal ? (
                    "Total"
                  ) : (
                    <span title={alcanceLabels.join(", ")}>
                      {c.alcanceItems.length} {alcanceUnidad}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-muted-foreground">{c.motivo ?? "—"}</td>
                <td className="px-4 py-3">
                  <BrandBadge variant={meta.variant}>
                    <span aria-label={`Estado: ${meta.label}`}>{meta.label}</span>
                  </BrandBadge>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-1">
                    {editable && (
                      <button
                        type="button"
                        onClick={() => onEdit(c)}
                        aria-label={`Editar cobertura de ${c.ausenteNombre ?? c.ausenteId}`}
                        title="Editar cobertura"
                        className="rounded-[8px] p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                    )}
                    {cancelable && (
                      <button
                        type="button"
                        onClick={() => onCancel(c)}
                        aria-label={`Cancelar cobertura de ${c.ausenteNombre ?? c.ausenteId}`}
                        title="Cancelar cobertura"
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
