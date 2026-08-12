"use client";

import { cn } from "@/shared/utils/cn";
import { selectableImportRow } from "../../hooks/use-contacts-import";
import type { ZoneContactPreviewRow } from "../../types";
import { StatusBadge, type StatusTone } from "../shared";

function contactLabel(apellido: string, nombre: string): string {
  if (!apellido.trim()) return "—";
  return nombre.trim() ? `${apellido}, ${nombre}` : apellido;
}

/** Celda diff: si la zona ya estaba configurada Y el valor entrante difiere
 * del actual, muestra el actual tachado arriba y el entrante abajo — para
 * que la tabla deje ver explícitamente qué se va a pisar en vez de esconderlo
 * en una lista plana. */
function DiffCell({
  alreadyConfigured,
  current,
  incoming,
}: {
  alreadyConfigured: boolean;
  current: string;
  incoming: string;
}) {
  const showDiff = alreadyConfigured && current.trim() !== incoming.trim();
  if (!showDiff) return <>{incoming.trim() || "—"}</>;
  return (
    <div className="flex flex-col">
      <span className="line-through text-muted-foreground text-[11px]">{current || "—"}</span>
      <span>{incoming || "—"}</span>
    </div>
  );
}

function statusFor(row: ZoneContactPreviewRow): { tone: StatusTone; label: string; title?: string } {
  if (row.error) return { tone: "atencion", label: "No se pudo resolver", title: row.error };
  if (row.already_configured) return { tone: "advertencia", label: "Ya configurada — se pisa" };
  if (!row.apellido.trim()) return { tone: "neutral", label: "Sin datos" };
  return { tone: "ok", label: "Nueva" };
}

interface ContactsImportTableProps {
  rows: readonly ZoneContactPreviewRow[];
  selected: ReadonlySet<string>;
  onToggle: (zone: string) => void;
  onToggleAll: () => void;
}

export function ContactsImportTable({ rows, selected, onToggle, onToggleAll }: ContactsImportTableProps) {
  const selectableRows = rows.filter(selectableImportRow);
  const allSelected = selectableRows.length > 0 && selectableRows.every((r) => selected.has(r.zone));
  const someSelected = selectableRows.some((r) => selected.has(r.zone));

  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full text-left font-body text-sm">
        <thead>
          <tr className="border-b border-border text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            <th scope="col" className="px-4 py-3">
              <input
                type="checkbox"
                checked={allSelected}
                ref={(el) => {
                  if (el) el.indeterminate = someSelected && !allSelected;
                }}
                onChange={onToggleAll}
                aria-label="Seleccionar todas las zonas disponibles"
                className="cursor-pointer accent-brand-orange"
                disabled={selectableRows.length === 0}
              />
            </th>
            <th scope="col" className="px-4 py-3">Zona</th>
            <th scope="col" className="px-4 py-3">Contacto</th>
            <th scope="col" className="px-4 py-3">Email</th>
            <th scope="col" className="px-4 py-3">Teléfono</th>
            <th scope="col" className="px-4 py-3">Estado</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const selectable = selectableImportRow(row);
            const isSelected = selected.has(row.zone);
            const status = statusFor(row);
            return (
              <tr
                key={row.zone}
                className={cn(
                  "border-b border-border last:border-0",
                  isSelected && "bg-brand-orange/5",
                )}
              >
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => onToggle(row.zone)}
                    disabled={!selectable}
                    aria-label={`Seleccionar zona ${row.zone}`}
                    className={cn(
                      "accent-brand-orange",
                      selectable ? "cursor-pointer" : "cursor-not-allowed opacity-30",
                    )}
                  />
                </td>
                <td className="px-4 py-3 font-semibold text-foreground">{row.zone}</td>
                <td className="px-4 py-3 text-foreground">
                  <DiffCell
                    alreadyConfigured={row.already_configured}
                    current={contactLabel(row.current_apellido, row.current_nombre)}
                    incoming={contactLabel(row.apellido, row.nombre)}
                  />
                </td>
                <td className="px-4 py-3 text-foreground">
                  <DiffCell
                    alreadyConfigured={row.already_configured}
                    current={row.current_email}
                    incoming={row.email}
                  />
                </td>
                <td className="px-4 py-3 text-foreground">
                  <DiffCell
                    alreadyConfigured={row.already_configured}
                    current={row.current_telefono}
                    incoming={row.telefono}
                  />
                </td>
                <td className="px-4 py-3">
                  <span title={status.title}>
                    <StatusBadge tone={status.tone}>{status.label}</StatusBadge>
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
