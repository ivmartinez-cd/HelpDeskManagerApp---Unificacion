import { cn } from "@/shared/utils/cn";
import type { DashboardResponse } from "../../types";

/** Fila de tiles KPI del Dashboard. Los 7 valores salen tal cual de
 * `GET /api/insumos/dashboard`: `totals.{pending,critical,urgent,warning,good,
 * loaded}` + `loadedToday`, con los umbrales de días en la etiqueta.
 *
 * Colores: semáforo rojo/amarillo/verde para severidad y naranja Institucional
 * para lo accionable. "Cargado" iba en celeste `#00a4e4` en el legacy — color
 * PROHIBIDO por el handoff, reemplazado por el gris MPS `#58595B`.
 *
 * "Cargado" (antes "Con pedido") cuenta SOLO pedidos propios verificados — un
 * pedido activo detectado por matching que nunca confirmó entrega no cuenta acá
 * (sigue en "Pendientes"/severidad, con badge de aviso en la fila).
 */

interface Tile {
  label: string;
  value: number;
  color: string;
  /** Resalta el tile con borde y fondo tintados (solo "Pendientes" con cola). */
  highlight?: boolean;
}

function tilesFor(dashboard: DashboardResponse): Tile[] {
  const { totals, thresholds, loadedToday } = dashboard;
  const pending = totals.pending ?? 0;
  return [
    { label: "Pendientes", value: pending, color: "#F7941D", highlight: pending > 0 },
    { label: `Críticos ≤${thresholds.critical}d`, value: totals.critical ?? 0, color: "#ef4444" },
    { label: `Urgentes ≤${thresholds.urgent}d`, value: totals.urgent ?? 0, color: "#F7941D" },
    { label: `Atención ≤${thresholds.warning}d`, value: totals.warning ?? 0, color: "#eab308" },
    { label: "OK", value: totals.good ?? 0, color: "#22c55e" },
    { label: "Cargado", value: totals.loaded ?? 0, color: "#3b82f6" },
    { label: "Cargados hoy", value: loadedToday, color: "#F7941D" },
  ];
}

interface DashboardTilesProps {
  dashboard: DashboardResponse | null;
  loading: boolean;
}

export function DashboardTiles({ dashboard, loading }: DashboardTilesProps) {
  if (!dashboard) {
    return (
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-7">
        {Array.from({ length: 7 }, (_, index) => (
          <div
            key={index}
            className="h-[76px] animate-pulse rounded-[12px] border border-border bg-muted/60"
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "grid grid-cols-2 gap-3 transition-opacity sm:grid-cols-4 xl:grid-cols-7",
        loading && "opacity-70",
      )}
    >
      {tilesFor(dashboard).map((tile) => (
        <div
          key={tile.label}
          className="flex flex-col items-center rounded-[12px] bg-card px-4 py-3 text-center"
          style={{
            border: `1.5px solid ${tile.color}`,
            background: tile.highlight ? `${tile.color}14` : undefined,
          }}
        >
          <p
            className="font-heading text-[22px] font-extrabold leading-none tabular-nums"
            style={{ color: tile.color }}
          >
            {tile.value}
          </p>
          <p className="mt-1.5 font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            {tile.label}
          </p>
        </div>
      ))}
    </div>
  );
}
