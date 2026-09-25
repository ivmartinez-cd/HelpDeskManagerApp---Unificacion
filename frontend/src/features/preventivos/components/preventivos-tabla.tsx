"use client";

import type { EquipoPreventivo, EstadoPreventivo, PreventivoSortKey } from "../types/preventivos";
import { BrandBadge } from "@/shared/components/ui/brand-form";
import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import type { OptionalSortState } from "@/shared/hooks/use-optional-table-sort";
import { Switch } from "@/shared/components/ui/switch";

/** El orden viene del backend (por defecto vencidos primero, más atrasado
 * arriba; o la columna que se toque); acá solo se mapea cada estado a un
 * color/etiqueta. */
export const ESTADO_META: Record<
  EstadoPreventivo,
  { label: string; variant: "neutral" | "accent" | "success" | "warning" | "danger" }
> = {
  vencido: { label: "Vencido", variant: "danger" },
  por_vencer: { label: "Por vencer", variant: "warning" },
  al_dia: { label: "Al día", variant: "success" },
  sin_preventivo: { label: "Sin preventivo", variant: "accent" },
  sin_frecuencia: { label: "Sin frecuencia", variant: "neutral" },
};

export function formatFecha(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

function formatFechaHora(iso: string): string {
  return new Date(iso).toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function FrecuenciaCell({ dias }: { dias: number | null }) {
  if (!dias) return <span className="text-muted-foreground">—</span>;
  return (
    <span className="tabular-nums text-foreground">
      {dias} días
    </span>
  );
}

function VencimientoCell({ equipo }: { equipo: EquipoPreventivo }) {
  if (!equipo.proximo_vencimiento) {
    if (equipo.fecha_tentativa) {
      return (
        <div className="leading-tight">
          <p className="tabular-nums text-muted-foreground">
            {formatFecha(equipo.fecha_tentativa)}
          </p>
          <p className="text-xs text-muted-foreground" title="Instalación + frecuencia, nunca hubo un preventivo real">
            tentativo
          </p>
        </div>
      );
    }
    return <span className="text-muted-foreground">—</span>;
  }
  return (
    <div className="leading-tight">
      <p className="tabular-nums text-foreground">{formatFecha(equipo.proximo_vencimiento)}</p>
      {equipo.dias_vencido !== null && (
        <p className="text-xs font-semibold text-destructive">
          hace {new Intl.NumberFormat("es-AR").format(equipo.dias_vencido)} días
        </p>
      )}
    </div>
  );
}

function HabilitacionCell({
  equipo,
  canUpdate,
  pending,
  onToggle,
}: {
  equipo: EquipoPreventivo;
  canUpdate: boolean;
  pending: boolean;
  onToggle: (equipo: EquipoPreventivo) => void;
}) {
  const habilitacion = equipo.habilitacion;
  return (
    <div className="flex items-center gap-2.5">
      <Switch
        checked={habilitacion !== null}
        disabled={!canUpdate || pending}
        label={`Habilitar preventivo de ${equipo.serie}`}
        onCheckedChange={() => onToggle(equipo)}
      />
      {habilitacion && (
        <div className="leading-tight">
          <p className="text-xs font-semibold text-foreground">{habilitacion.habilitado_por}</p>
          <p
            className="text-[11px] text-muted-foreground"
            title={habilitacion.nota ?? undefined}
          >
            {formatFechaHora(habilitacion.habilitado_en)}
            {habilitacion.nota ? " · con nota" : ""}
          </p>
        </div>
      )}
    </div>
  );
}

const COLUMNAS: SortableColumn<PreventivoSortKey>[] = [
  { key: "cliente", label: "Cliente" },
  { key: "sucursal", label: "Sucursal" },
  { key: "equipo", label: "Equipo" },
  { key: "ultimo_preventivo", label: "Últ. preventivo" },
  { key: "frecuencia", label: "Frecuencia" },
  { key: "vencimiento", label: "Próx. vencimiento" },
  // Por urgencia: vencido, sin preventivo, por vencer, al día, sin frecuencia.
  { key: "estado", label: "Estado" },
  { key: "habilitado", label: "Habilitado" },
];

interface PreventivosTablaProps {
  rows: EquipoPreventivo[];
  sort: OptionalSortState<PreventivoSortKey>;
  onToggleSort: (key: PreventivoSortKey) => void;
  canUpdate: boolean;
  pendingId: number | null;
  onToggleHabilitacion: (equipo: EquipoPreventivo) => void;
}

export function PreventivosTabla({
  rows,
  sort,
  onToggleSort,
  canUpdate,
  pendingId,
  onToggleHabilitacion,
}: PreventivosTablaProps) {
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full min-w-[1080px] text-left">
        <thead>
          <tr className="border-b border-border font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            {COLUMNAS.map((c) => (
              <SortableHeader
                key={c.key}
                column={c}
                sort={sort}
                onToggleSort={onToggleSort}
                thClassName="px-4 py-2.5"
              />
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((e) => {
            const meta = ESTADO_META[e.estado];
            return (
              <tr key={e.id_maquina} className="font-body text-sm hover:bg-muted/30">
                <td
                  className="max-w-[200px] truncate px-4 py-3 font-semibold text-foreground"
                  title={e.cliente}
                >
                  {e.cliente}
                </td>
                <td
                  className="max-w-[170px] truncate px-4 py-3 text-muted-foreground"
                  title={e.sucursal}
                >
                  {e.sucursal}
                </td>
                <td className="max-w-[230px] px-4 py-3">
                  <p className="font-mono text-xs font-semibold text-foreground">{e.serie}</p>
                  <p className="truncate text-xs text-muted-foreground" title={e.modelo}>
                    {e.modelo}
                  </p>
                </td>
                <td className="px-4 py-3 text-muted-foreground">
                  {e.fecha_ultimo_preventivo ? (
                    <span className="tabular-nums">{formatFecha(e.fecha_ultimo_preventivo)}</span>
                  ) : (
                    <span>—</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <FrecuenciaCell dias={e.frecuencia_dias} />
                </td>
                <td className="px-4 py-3">
                  <VencimientoCell equipo={e} />
                </td>
                <td className="px-4 py-3">
                  <BrandBadge variant={meta.variant}>{meta.label}</BrandBadge>
                </td>
                <td className="px-4 py-3">
                  <HabilitacionCell
                    equipo={e}
                    canUpdate={canUpdate}
                    pending={pendingId === e.id_maquina}
                    onToggle={onToggleHabilitacion}
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
