import type { ReactNode } from "react";
import type { CardId, LayoutRow } from "../config/dashboard-registry";

/** Grid de viewport fijo del cuerpo de Inicio (≥ xl): filas de alto
 * proporcional (`grid-template-rows` en fr) y, dentro de cada fila, columnas
 * proporcionales al peso de cada card visible. Las cards llenan su celda y
 * scrollean adentro — así el alto lo dicta el viewport y nunca aparece scroll
 * de página. Por debajo de xl (notebook angosta, tablet) las filas se apilan
 * con alto natural y scrollea el <main>: fallback declarado, no silencioso. */
export function DashboardGrid({
  rows,
  render,
}: {
  rows: LayoutRow[];
  render: (id: CardId) => ReactNode;
}) {
  return (
    <div
      data-testid="dashboard-grid"
      className="flex flex-col gap-3 short:gap-2.5 xl:grid xl:min-h-0 xl:flex-1"
      style={{ gridTemplateRows: rows.map((r) => `minmax(0, ${r.h}fr)`).join(" ") }}
    >
      {rows.map((row, i) => (
        <div
          key={i}
          className="flex flex-col gap-3 short:gap-2.5 xl:grid xl:min-h-0"
          style={{ gridTemplateColumns: row.cells.map((c) => `minmax(0, ${c.w}fr)`).join(" ") }}
        >
          {row.cells.map((cell) => (
            <div key={cell.id} data-card={cell.id} className="min-h-0 min-w-0">
              {render(cell.id)}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
