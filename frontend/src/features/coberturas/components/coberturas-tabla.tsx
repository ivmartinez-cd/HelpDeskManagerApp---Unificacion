"use client";

import { useMemo } from "react";
import { ArrowLeftRight, Ban, Pencil } from "lucide-react";
import type {
  Cobertura,
  CoberturaOperadorOption,
  FilaCoberturas,
  Intercambio,
} from "../types/coberturas";
import { ESTADO_META, formatFechaCorta } from "../lib/estado";
import { estadoFila, filaKey, nombreOperadorA, nombreOperadorB } from "../lib/intercambios";
import { BrandBadge } from "@/shared/components/ui/brand-form";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { UserAvatar } from "@/shared/components/ui/user-avatar";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";

type CoberturasSortKey = "ausente" | "reemplazante" | "desde" | "estado";
const COBERTURAS_SORT_KEYS: readonly CoberturasSortKey[] = [
  "ausente", "reemplazante", "desde", "estado",
];

interface CoberturasTablaProps {
  rows: FilaCoberturas[];
  operadorMeta: Map<string, CoberturaOperadorOption>;
  alcanceLabelOf: (id: string) => string;
  alcanceUnidad: string;
  canEdit: boolean;
  canCancel: boolean;
  onEdit: (fila: FilaCoberturas) => void;
  onCancel: (fila: FilaCoberturas) => void;
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

/** La "cobertura de referencia" de una fila: la común, o la ida del
 * intercambio (las dos mitades comparten fechas, estado y motivo). */
function referencia(fila: FilaCoberturas): Cobertura {
  return fila.tipo === "cobertura" ? fila.cobertura : fila.intercambio.ida;
}

function descripcionFila(fila: FilaCoberturas): string {
  if (fila.tipo === "cobertura") {
    return `cobertura de ${fila.cobertura.ausenteNombre ?? fila.cobertura.ausenteId}`;
  }
  const i = fila.intercambio;
  return `intercambio de ${nombreOperadorA(i)} y ${nombreOperadorB(i)}`;
}

function AlcanceCell({
  fila,
  alcanceLabelOf,
  alcanceUnidad,
}: {
  fila: FilaCoberturas;
  alcanceLabelOf: (id: string) => string;
  alcanceUnidad: string;
}) {
  const mitades: Cobertura[] =
    fila.tipo === "cobertura" ? [fila.cobertura] : [fila.intercambio.ida, fila.intercambio.vuelta];
  if (mitades.every((c) => c.alcanceTotal)) return <>Total</>;
  const items = mitades.flatMap((c) => (c.alcanceTotal ? [] : c.alcanceItems));
  return (
    <span title={items.map(alcanceLabelOf).join(", ")}>
      {items.length} {alcanceUnidad}
    </span>
  );
}

function IntercambioCell({
  intercambio,
  operadorMeta,
}: {
  intercambio: Intercambio;
  operadorMeta: Map<string, CoberturaOperadorOption>;
}) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <OperadorCell
        id={intercambio.ida.ausenteId}
        nombre={intercambio.ida.ausenteNombre}
        meta={operadorMeta.get(intercambio.ida.ausenteId)}
      />
      <ArrowLeftRight
        className="h-4 w-4 shrink-0 text-brand-orange"
        aria-label="intercambia con"
      />
      <OperadorCell
        id={intercambio.vuelta.ausenteId}
        nombre={intercambio.vuelta.ausenteNombre}
        meta={operadorMeta.get(intercambio.vuelta.ausenteId)}
      />
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
    const getSv = (fila: FilaCoberturas) => {
      const c = referencia(fila);
      switch (sort.key) {
        case "ausente": return c.ausenteNombre ?? c.ausenteId;
        case "reemplazante": return c.reemplazanteNombre ?? c.reemplazanteId;
        case "desde": return c.desde;
        case "estado": return estadoFila(fila);
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
          {sorted.map((fila) => {
            const c = referencia(fila);
            const estado = estadoFila(fila);
            const meta = ESTADO_META[estado];
            // Solo las reglas aún en juego se pueden editar/cancelar: una
            // vencida o cancelada es un registro histórico (ADR-013).
            const mutable = estado === "activa" || estado === "programada";
            const editable = canEdit && mutable;
            const cancelable = canCancel && mutable;
            const descripcion = descripcionFila(fila);
            return (
              <tr key={filaKey(fila)} className="font-body text-sm">
                {fila.tipo === "cobertura" ? (
                  <>
                    <td className="px-4 py-3">
                      <OperadorCell id={c.ausenteId} nombre={c.ausenteNombre} meta={operadorMeta.get(c.ausenteId)} />
                    </td>
                    <td className="px-4 py-3">
                      <OperadorCell id={c.reemplazanteId} nombre={c.reemplazanteNombre} meta={operadorMeta.get(c.reemplazanteId)} />
                    </td>
                  </>
                ) : (
                  // Un intercambio no tiene "ausente" ni "reemplazante": ocupa las
                  // dos columnas con A ⇄ B (ADR-026).
                  <td className="px-4 py-3" colSpan={2}>
                    <IntercambioCell intercambio={fila.intercambio} operadorMeta={operadorMeta} />
                  </td>
                )}
                <td className="px-4 py-3 leading-tight text-muted-foreground">
                  <p>{formatFechaCorta(c.desde)}</p>
                  <p>→ {formatFechaCorta(c.hasta)}</p>
                </td>
                <td className="px-4 py-3 text-muted-foreground">
                  <AlcanceCell fila={fila} alcanceLabelOf={alcanceLabelOf} alcanceUnidad={alcanceUnidad} />
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
                        onClick={() => onEdit(fila)}
                        aria-label={`Editar ${descripcion}`}
                        title={fila.tipo === "cobertura" ? "Editar cobertura" : "Editar intercambio"}
                        className="rounded-[8px] p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                    )}
                    {cancelable && (
                      <button
                        type="button"
                        onClick={() => onCancel(fila)}
                        aria-label={`Cancelar ${descripcion}`}
                        title={fila.tipo === "cobertura" ? "Cancelar cobertura" : "Cancelar intercambio"}
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
