"use client";

import type { EquipoPreventivo, EstadoPreventivo } from "../types/preventivos";
import { BrandBadge } from "@/shared/components/ui/brand-form";
import { Switch } from "@/shared/components/ui/switch";

/** El orden ya viene del backend (vencidos primero, más atrasado arriba);
 * acá solo se mapea cada estado a un color/etiqueta. */
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

interface PreventivosTablaProps {
  rows: EquipoPreventivo[];
  canUpdate: boolean;
  pendingId: number | null;
  onToggleHabilitacion: (equipo: EquipoPreventivo) => void;
}

export function PreventivosTabla({
  rows,
  canUpdate,
  pendingId,
  onToggleHabilitacion,
}: PreventivosTablaProps) {
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full min-w-[1080px] text-left">
        <thead>
          <tr className="border-b border-border font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            <th className="px-4 py-2.5">Cliente</th>
            <th className="px-4 py-2.5">Sucursal</th>
            <th className="px-4 py-2.5">Equipo</th>
            <th className="px-4 py-2.5">Últ. preventivo</th>
            <th className="px-4 py-2.5">Frecuencia</th>
            <th className="px-4 py-2.5">Próx. vencimiento</th>
            <th className="px-4 py-2.5">Estado</th>
            <th className="px-4 py-2.5">Habilitado</th>
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
