"use client";

import {
  Calendar,
  ChevronDown,
  ChevronUp,
  History,
  Pencil,
  Trash2,
  TrendingDown,
  TrendingUp,
  Zap,
} from "lucide-react";
import { useState } from "react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { formatARS, formatFechaDia } from "../lib/format";
import type { Tarifario } from "../types/liquidaciones";

// Port de components/tarifarios/{ServiceTarifaRow,TarifarioHistoryTimeline}.tsx
// del legacy Liquidacion-Prestadores, reestilado a los tokens del monorepo
// (brand-orange/success en vez de indigo/emerald, dark-aware).

export interface GrupoTarifa {
  tipoServicio: string;
  zona: string | null;
  historial: Tarifario[];
  vigente: Tarifario | null;
}

export function agruparTarifarios(tarifarios: Tarifario[]): GrupoTarifa[] {
  const hoy = new Date().toISOString().split("T")[0];
  const grupos = new Map<string, GrupoTarifa>();
  for (const t of tarifarios) {
    const key = `${t.tipoServicio}::${t.zona ?? ""}`;
    let grupo = grupos.get(key);
    if (!grupo) {
      grupo = { tipoServicio: t.tipoServicio, zona: t.zona, historial: [], vigente: null };
      grupos.set(key, grupo);
    }
    grupo.historial.push(t);
  }
  for (const grupo of grupos.values()) {
    grupo.historial.sort((a, b) => b.vigenciaDesde.localeCompare(a.vigenciaDesde));
    grupo.vigente =
      grupo.historial.find(
        (t) => t.vigenciaDesde <= hoy && (t.vigenciaHasta === null || t.vigenciaHasta >= hoy),
      ) ?? grupo.historial[0] ?? null;
  }
  return [...grupos.values()].sort(
    (a, b) =>
      a.tipoServicio.localeCompare(b.tipoServicio) || (a.zona ?? "").localeCompare(b.zona ?? ""),
  );
}

function VariacionBadge({ actual, anterior }: { actual: number; anterior: number }) {
  if (!anterior) return null;
  const pct = ((actual - anterior) / anterior) * 100;
  const sube = pct > 0;
  const baja = pct < 0;
  const cls = sube
    ? "bg-success/10 text-success"
    : baja
      ? "bg-destructive/10 text-destructive"
      : "bg-muted text-muted-foreground";
  const Icono = baja ? TrendingDown : TrendingUp;
  return (
    <span className={`inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 font-body text-[10px] font-bold ${cls}`}>
      <Icono className="h-2.5 w-2.5" />
      {pct === 0 ? "Sin cambios" : `${sube ? "+" : ""}${pct.toFixed(1)}%`}
    </span>
  );
}

function TarifarioHistoryTimeline({
  grupo, canEdit, onEdit, onDelete,
}: {
  grupo: GrupoTarifa; canEdit: boolean; onEdit: (t: Tarifario) => void; onDelete: (id: string) => void;
}) {
  return (
    <div className="mt-4 rounded-[12px] border-t border-dashed border-border bg-muted/20 p-4 pt-4">
      <h5 className="mb-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
        Línea de tiempo de tarifas
      </h5>
      <div className="relative space-y-6 border-l border-border pl-6">
        {grupo.historial.map((tarifa, idx) => {
          const anterior = grupo.historial[idx + 1];
          const esVigente = grupo.vigente?.id === tarifa.id;
          return (
            <div key={tarifa.id} className="relative">
              <span
                className={`absolute -left-[31px] top-1.5 h-3.5 w-3.5 rounded-full border-2 bg-card ${
                  esVigente ? "border-brand-orange ring-4 ring-brand-orange/15" : "border-border"
                }`}
              />
              <div className="flex flex-col justify-between gap-2 md:flex-row md:items-center">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-body text-sm font-bold text-foreground">
                      {formatARS(tarifa.costoServicio)}
                    </span>
                    <span className="font-body text-xs text-muted-foreground">|</span>
                    <span className="font-body text-xs font-medium text-muted-foreground">
                      {formatARS(tarifa.costoKm)}/km
                    </span>
                    {esVigente && (
                      <span className="rounded-full bg-success/10 px-2 py-0.5 font-body text-[10px] font-bold text-success">
                        Vigente hoy
                      </span>
                    )}
                    {anterior && (
                      <VariacionBadge actual={tarifa.costoServicio} anterior={anterior.costoServicio} />
                    )}
                    {!anterior && (
                      <span className="rounded-full bg-muted px-2 py-0.5 font-body text-[10px] font-bold text-muted-foreground">
                        Inicial
                      </span>
                    )}
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-1.5 font-body text-xs text-muted-foreground">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>Periodo:</span>
                    <span className="font-semibold text-foreground">{formatFechaDia(tarifa.vigenciaDesde)}</span>
                    <span>al</span>
                    <span className="font-semibold text-foreground">
                      {tarifa.vigenciaHasta ? formatFechaDia(tarifa.vigenciaHasta) : "actualidad"}
                    </span>
                  </div>
                </div>
                {canEdit && (
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => onEdit(tarifa)}
                      aria-label="Editar tarifa"
                      className="rounded-[6px] p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-brand-orange"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => onDelete(tarifa.id)}
                      aria-label="Eliminar tarifa"
                      className="rounded-[6px] p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-destructive"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function GrupoTarifaRow({
  grupo, canEdit = true, onActualizar, onEdit, onDelete,
}: {
  grupo: GrupoTarifa;
  /** `liquidaciones.update` (ADR-029): sin esto el historial es solo lectura. */
  canEdit?: boolean;
  onActualizar: (grupo: GrupoTarifa) => void;
  onEdit: (t: Tarifario) => void;
  onDelete: (id: string) => void;
}) {
  const [historialAbierto, setHistorialAbierto] = useState(false);
  const Chevron = historialAbierto ? ChevronUp : ChevronDown;

  return (
    <div className="p-5 transition-colors hover:bg-muted/20">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-[10px] bg-muted p-2.5">
            <Zap className="h-4 w-4 text-brand-orange" />
          </div>
          <div>
            <h4 className="font-heading text-sm font-bold capitalize text-foreground">
              {grupo.tipoServicio.replace(/_/g, " ")}
            </h4>
            <p className="mt-0.5 flex items-center gap-1 font-body text-xs text-muted-foreground">
              <span>Zona:</span>
              <span className="rounded-[6px] bg-muted px-1.5 py-0.5 font-semibold text-foreground">
                {grupo.zona || "Toda la cobertura"}
              </span>
            </p>
          </div>
        </div>

        {grupo.vigente && (
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex flex-col rounded-[10px] border border-brand-orange/20 bg-brand-orange/10 px-4 py-2 text-right">
              <span className="font-body text-[10px] font-bold uppercase tracking-wide text-brand-orange">
                Costo servicio
              </span>
              <span className="mt-0.5 font-body text-sm font-bold text-foreground">
                {formatARS(grupo.vigente.costoServicio)}
              </span>
            </div>
            <div className="flex flex-col rounded-[10px] border border-border bg-muted/40 px-4 py-2 text-right">
              <span className="font-body text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
                Costo KM
              </span>
              <span className="mt-0.5 font-body text-sm font-bold text-foreground">
                {formatARS(grupo.vigente.costoKm)}/km
              </span>
            </div>
            <div className="flex flex-col rounded-[10px] border border-success/20 bg-success/10 px-4 py-2 text-right">
              <span className="font-body text-[10px] font-bold uppercase tracking-wide text-success">
                Desde
              </span>
              <span className="mt-0.5 font-body text-xs font-semibold text-foreground">
                {formatFechaDia(grupo.vigente.vigenciaDesde)}
              </span>
            </div>
            <div className="ml-1 flex items-center gap-1.5">
              {canEdit && (
                <BrandButton size="sm" variant="outline" onClick={() => onActualizar(grupo)}>
                  Actualizar
                </BrandButton>
              )}
              <BrandButton size="sm" variant="outline" onClick={() => setHistorialAbierto((v) => !v)}>
                <History className="h-3.5 w-3.5" />
                Historial ({grupo.historial.length})
                <Chevron className="h-3 w-3" />
              </BrandButton>
            </div>
          </div>
        )}
      </div>

      {historialAbierto && (
        <TarifarioHistoryTimeline grupo={grupo} canEdit={canEdit} onEdit={onEdit} onDelete={onDelete} />
      )}
    </div>
  );
}
