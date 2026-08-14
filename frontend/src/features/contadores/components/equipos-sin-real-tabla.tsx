"use client";

import type {
  EquipoSinReal,
  EquiposSinRealSortKey,
  SeveridadSinReal,
} from "../types/equipos-sin-real";
import { BrandBadge } from "@/shared/components/ui/brand-form";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import type { SortState } from "@/shared/hooks/use-table-sort";

/** Colores de alerta por severidad — los umbrales los decide el backend
 * (`severidad_sin_real.py`), acá solo se mapea cada nivel a un color. */
export const SEVERIDAD_META: Record<
  SeveridadSinReal,
  { label: string; variant: "neutral" | "accent" | "warning" | "danger" }
> = {
  critico: { label: "Crítico", variant: "danger" },
  alto: { label: "Alto", variant: "accent" },
  medio: { label: "Medio", variant: "warning" },
  bajo: { label: "Bajo", variant: "neutral" },
};

const numberFormat = new Intl.NumberFormat("es-AR");

export function formatFecha(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

interface EquiposSinRealTablaProps {
  rows: EquipoSinReal[];
  sort: SortState<EquiposSinRealSortKey>;
  onToggleSort: (key: EquiposSinRealSortKey) => void;
}

function OperadorCell({ equipo }: { equipo: EquipoSinReal }) {
  if (!equipo.operador_nombre) {
    return <span className="text-muted-foreground">—</span>;
  }
  return (
    <div className="flex items-center gap-2">
      <span
        aria-hidden="true"
        className="h-2.5 w-2.5 flex-none rounded-full bg-muted-foreground"
        style={equipo.operador_color ? { backgroundColor: equipo.operador_color } : undefined}
      />
      <span className="truncate text-foreground">{equipo.operador_nombre}</span>
    </div>
  );
}

function UltimoRealCell({ equipo }: { equipo: EquipoSinReal }) {
  if (equipo.nunca_tuvo_real) {
    return (
      <div className="leading-tight">
        <BrandBadge variant="danger">Nunca</BrandBadge>
        <p className="mt-1 font-body text-xs text-muted-foreground">
          instalado {formatFecha(equipo.fecha_referencia)}
        </p>
      </div>
    );
  }
  return <span>{formatFecha(equipo.fecha_ultimo_real ?? equipo.fecha_referencia)}</span>;
}

export function EquiposSinRealTabla({ rows, sort, onToggleSort }: EquiposSinRealTablaProps) {
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full min-w-[1120px] text-left">
        <thead>
          <tr className="border-b border-border font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            <th className="px-4 py-2.5">Serie</th>
            <SortableHeader column={{ key: "modelo", label: "Modelo" }} sort={sort} onToggleSort={onToggleSort} thClassName="px-4 py-2.5" />
            <SortableHeader column={{ key: "cliente", label: "Cliente" }} sort={sort} onToggleSort={onToggleSort} thClassName="px-4 py-2.5" />
            <SortableHeader column={{ key: "sucursal", label: "Sucursal" }} sort={sort} onToggleSort={onToggleSort} thClassName="px-4 py-2.5" />
            <SortableHeader column={{ key: "operador", label: "Operador" }} sort={sort} onToggleSort={onToggleSort} thClassName="px-4 py-2.5" />
            <th className="px-4 py-2.5">Últ. real</th>
            <SortableHeader column={{ key: "meses", label: "Meses sin real" }} sort={sort} onToggleSort={onToggleSort} thClassName="px-4 py-2.5" />
            <th className="px-4 py-2.5 text-right">Prom. 3M</th>
            <th className="px-4 py-2.5">Estado</th>
            <th className="px-4 py-2.5">Observaciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((e) => {
            const meta = SEVERIDAD_META[e.severidad];
            return (
              <tr key={e.id_maquina} className="font-body text-sm hover:bg-muted/30">
                <td className="px-4 py-3">
                  <p className="font-mono text-xs font-semibold text-foreground">{e.serie}</p>
                  {e.propiedad && e.propiedad !== "CD1 (CDSA)" && (
                    <p className="text-xs text-muted-foreground">Prop.: {e.propiedad}</p>
                  )}
                </td>
                <td className="max-w-[220px] px-4 py-3">
                  <p className="truncate text-foreground" title={e.modelo}>
                    {e.modelo}
                  </p>
                  {e.tecnologia && (
                    <p className="text-xs uppercase text-muted-foreground">{e.tecnologia}</p>
                  )}
                </td>
                <td className="max-w-[200px] truncate px-4 py-3 font-semibold text-foreground" title={e.cliente}>
                  {e.cliente}
                </td>
                <td className="max-w-[180px] truncate px-4 py-3 text-muted-foreground" title={e.sucursal}>
                  {e.sucursal}
                </td>
                <td className="max-w-[160px] px-4 py-3">
                  <OperadorCell equipo={e} />
                </td>
                <td className="px-4 py-3 text-muted-foreground">
                  <UltimoRealCell equipo={e} />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="min-w-[2ch] text-right text-base font-bold tabular-nums text-foreground">
                      {e.meses_sin_real}
                    </span>
                    <BrandBadge variant={meta.variant}>{meta.label}</BrandBadge>
                  </div>
                </td>
                <td
                  className="px-4 py-3 text-right tabular-nums text-muted-foreground"
                  title={`Impresiones por mes (reciente → atrás): ${numberFormat.format(e.im1)} · ${numberFormat.format(e.im2)} · ${numberFormat.format(e.im3)}`}
                >
                  {numberFormat.format(e.imp_prom_3m)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                  {e.estado_maquina}
                </td>
                <td className="max-w-[240px] truncate px-4 py-3 text-xs text-muted-foreground" title={e.observaciones || undefined}>
                  {e.observaciones || "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
