import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import type { Reporte } from "../../types/reporte";
import { formatearEntero } from "../../lib/periodos";

/** Los 3 KPIs del legacy, sobre la selección filtrada. */
export function KpisReporte({ reporte }: { reporte: Reporte }) {
  const { kpis } = reporte;
  const hayCasos = kpis.total > 0;
  return (
    <KpiGrid>
      <KpiTile
        label="Total incidentes"
        value={formatearEntero(kpis.total)}
        tone="orange"
        hint={`en ${reporte.rango_etiqueta}`}
      />
      <KpiTile
        label="Categoría principal"
        value={kpis.categoria_principal}
        hint={
          hayCasos
            ? `${formatearEntero(kpis.categoria_principal_cantidad)} casos (${kpis.categoria_principal_pct}%)`
            : "Sin incidentes"
        }
      />
      <KpiTile
        label="Sucursal principal"
        value={kpis.sucursal_principal}
        hint={hayCasos ? `${formatearEntero(kpis.sucursal_principal_cantidad)} incidentes` : "Sin incidentes"}
      />
    </KpiGrid>
  );
}
