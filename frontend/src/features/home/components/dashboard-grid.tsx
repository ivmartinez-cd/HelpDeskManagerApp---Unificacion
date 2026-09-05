import type { ReactNode } from "react";
import type { CardId, LayoutRow } from "../config/dashboard-registry";

/** Grid de viewport fijo del cuerpo de Inicio (≥ xl): filas de alto
 * proporcional (`grid-template-rows` en fr) y, dentro de cada fila, columnas
 * proporcionales al peso de cada card visible. Las cards llenan su celda y
 * scrollean adentro — así el alto lo dicta el viewport y nunca aparece scroll
 * de página. Por debajo de xl (notebook angosta, tablet) las filas se apilan
 * con alto natural y scrollea el <main>: fallback declarado, no silencioso.
 *
 * `totalH` es el alto diseñado de la vista completa (`viewTotalHeight`): si
 * al usuario le desaparece una fila entera, la diferencia queda como una
 * última fila vacía en vez de estirar las filas que sí tiene — evitar cards
 * infladas con hueco interno pesa más que evitar un margen en blanco al pie. */
export function DashboardGrid({
  rows,
  totalH,
  render,
}: {
  rows: LayoutRow[];
  totalH: number;
  render: (id: CardId) => ReactNode;
}) {
  const visibleH = rows.reduce((sum, r) => sum + r.h, 0);
  const espacio = Math.max(0, totalH - visibleH);
  const gridTemplateRows = rows
    .map((r) => `minmax(0, ${r.h}fr)`)
    .concat(espacio > 0 ? [`${espacio}fr`] : [])
    .join(" ");

  return (
    <div
      data-testid="dashboard-grid"
      className="flex flex-col gap-3 short:gap-2.5 xl:grid xl:min-h-0 xl:flex-1"
      style={{ gridTemplateRows }}
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
      {espacio > 0 && <div aria-hidden="true" className="hidden xl:block" data-testid="dashboard-grid-spacer" />}
    </div>
  );
}
