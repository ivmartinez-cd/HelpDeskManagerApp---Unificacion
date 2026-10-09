"use client";

import type { IncidenteBono } from "../types/bono-tecnicos";
import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import { useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";
import { formatPlainDate } from "@/shared/utils/date-arg";
import { incidentUrl } from "@/shared/utils/incident-link";

type SortKey = "id_incidente" | "fecha_cierre" | "cliente" | "sucursal" | "nro_serie";

const COLUMNAS: SortableColumn<SortKey>[] = [
  { key: "id_incidente", label: "ID" },
  { key: "fecha_cierre", label: "Cierre" },
  { key: "cliente", label: "Cliente" },
  { key: "sucursal", label: "Sucursal" },
  { key: "nro_serie", label: "Nro. Serie" },
];

const valorOrden = (i: IncidenteBono, key: SortKey) => i[key];

/** `Fecha_Cierre` llega de Siges sin huso (hora local argentina): se corta el
 * texto tal cual, sin pasar por `Date`, para no correr el día según el
 * navegador (ver `date-arg.ts`). */
function formatCierre(fecha: string | null): string {
  if (!fecha) return "—";
  const hora = fecha.slice(11, 16);
  return hora ? `${formatPlainDate(fecha.slice(0, 10))} ${hora}` : formatPlainDate(fecha);
}

/** Tabla de incidentes de una categoría del bono — compartida por el modal de
 * gerencia (`BonoTecnicoDetalleModal`) y "Mis incidentes" del técnico. */
export function IncidentesCategoriaSection({
  label,
  incidentes,
}: {
  label: string;
  incidentes: IncidenteBono[];
}) {
  const { sort, toggleSort } = useOptionalTableSort<SortKey>(["fecha_cierre"]);
  const filas = useSortedRows(incidentes, sort, valorOrden);
  return (
    <section className="flex flex-col gap-2">
      <h3 className="font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
        {label} ({incidentes.length})
      </h3>
      {incidentes.length === 0 ? (
        <p className="font-body text-xs text-muted-foreground">Sin incidentes en el período.</p>
      ) : (
        <div className="overflow-x-auto thin-scrollbar rounded-[8px] border border-border">
          <table className="w-full border-collapse font-body text-xs">
            <thead>
              <tr className="border-b border-border text-left text-muted-foreground">
                {COLUMNAS.map((c) => (
                  <SortableHeader
                    key={c.key}
                    column={c}
                    sort={sort}
                    onToggleSort={toggleSort}
                    thClassName="whitespace-nowrap px-3 py-1.5 font-semibold"
                  />
                ))}
              </tr>
            </thead>
            <tbody>
              {filas.map((i) => (
                <tr key={i.id_incidente} className="border-b border-border/50 last:border-b-0">
                  <td className="whitespace-nowrap px-3 py-1.5 tabular-nums">
                    <a
                      href={incidentUrl(i.id_incidente)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-semibold text-brand-orange hover:underline"
                    >
                      {i.id_incidente}
                    </a>
                  </td>
                  <td className="whitespace-nowrap px-3 py-1.5 tabular-nums">
                    {formatCierre(i.fecha_cierre)}
                  </td>
                  <td className="px-3 py-1.5">{i.cliente}</td>
                  <td className="px-3 py-1.5">{i.sucursal}</td>
                  <td className="px-3 py-1.5">{i.nro_serie}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
