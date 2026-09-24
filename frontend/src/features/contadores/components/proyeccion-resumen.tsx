"use client";

import { RotateCcw, X } from "lucide-react";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import type { RestauracionDecisiones, TableroProyeccion } from "../types/proyeccion";

/** KPIs y banner de restauración de `GrillaEstimacion.razor` (v1.7). */

/** `Pct` del legacy: sobre la cantidad de FILAS (no de máquinas), `{x:0}%`. */
function pct(n: number, totalFilas: number): string {
  if (totalFilas === 0) return "—";
  return `${Math.round((n * 100) / totalFilas)}%`;
}

export function ProyeccionKpis({ tablero }: { tablero: TableroProyeccion }) {
  const { resumen } = tablero;
  const filas = tablero.filas.length;
  return (
    <KpiGrid className="sm:grid-cols-3 lg:grid-cols-5">
      <KpiTile
        label="Contadores cargados"
        value={String(resumen.reales)}
        hint={`${pct(resumen.reales, filas)} del proceso`}
      />
      <KpiTile
        label="Estimados"
        value={String(resumen.estimados)}
        tone="orange"
        hint={`${pct(resumen.estimados, filas)} — propuestos por la app`}
      />
      <KpiTile
        label="Pendientes"
        value={String(resumen.pendientes)}
        tone="danger"
        hint={`${pct(resumen.pendientes, filas)} — requieren operador`}
      />
      <KpiTile
        label="Sospechosos"
        value={String(resumen.sospechosos)}
        tone="danger"
        hint="salto imposible o >3× promedio"
      />
      <KpiTile label="Total equipos" value={String(resumen.total)} hint="parque del proceso" />
    </KpiGrid>
  );
}

interface BannerProps {
  restauracion: RestauracionDecisiones;
  onDescartar: () => void;
  onCerrar: () => void;
}

export function ProyeccionBannerRestauracion({ restauracion, onDescartar, onCerrar }: BannerProps) {
  const { restauradas, descartadas } = restauracion;
  return (
    <div className="flex items-center gap-3 rounded-[8px] border border-info/40 bg-info/10 px-4 py-2.5 text-sm">
      <RotateCcw className="h-4 w-4 shrink-0 text-info" aria-hidden />
      <span className="flex-1">
        Restauramos <strong>{restauradas}</strong> decisi{restauradas === 1 ? "ón" : "ones"} de una sesión
        anterior.
        {descartadas > 0 && (
          <span className="ml-1 text-muted-foreground">
            {descartadas} descartada{descartadas === 1 ? "" : "s"} (ya tienen contador real o no se pudieron
            reconstruir).
          </span>
        )}
      </span>
      <button
        type="button"
        onClick={onDescartar}
        title="Descartar lo restaurado y empezar de cero"
        className="shrink-0 rounded-[8px] border border-info px-3 py-1 text-xs font-semibold text-info hover:bg-info hover:text-background"
      >
        Descartar y empezar limpio
      </button>
      <button type="button" onClick={onCerrar} title="Ocultar" className="text-muted-foreground hover:text-foreground">
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
