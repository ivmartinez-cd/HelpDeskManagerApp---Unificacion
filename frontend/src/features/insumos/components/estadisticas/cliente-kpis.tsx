import { EMPTY_VALUE, formatNumber, formatPercent, formatPlainDate } from "../../utils/format";
import { KpiGrid, KpiTile } from "./kpi-tile";
import type { CustomerDetailResponse } from "../../types";

/** Tiles KPI del detalle de cliente. Todos los números vienen del backend,
 * incluidos los del período anterior (`previousCreated`/`previousFailed`) y el
 * reparto auto/manual (`autoPct`): acá no se calcula nada salvo el delta. */
export function KpisCliente({ data }: { data: CustomerDetailResponse }) {
  const previousPeriod = `${formatPlainDate(data.previousStartDate)} – ${formatPlainDate(
    data.previousEndDate,
  )}`;

  return (
    <KpiGrid>
      <KpiTile
        label="Pedidos creados"
        value={formatNumber(data.totalCreated)}
        tone="orange"
        delta={{
          current: data.totalCreated,
          previous: data.previousCreated,
          periodLabel: previousPeriod,
        }}
      />
      <KpiTile
        label="Pedidos fallidos"
        value={formatNumber(data.totalFailed)}
        tone={data.totalFailed > 0 ? "danger" : "neutral"}
        delta={{
          current: data.totalFailed,
          previous: data.previousFailed,
          periodLabel: previousPeriod,
        }}
      />
      <KpiTile
        label="Tasa de éxito"
        value={formatPercent(data.successRate)}
        hint="Pedidos cargados sin error sobre el total"
      />
      <KpiTile
        label="Promedio diario"
        value={data.dailyAverage.toLocaleString("es-AR", { maximumFractionDigits: 1 })}
        hint="Pedidos creados por día del período"
      />
      <KpiTile
        label="Día pico"
        value={data.peakDay ? formatPlainDate(data.peakDay) : EMPTY_VALUE}
        hint={data.peakDay ? `${formatNumber(data.peakDayCount)} pedidos ese día` : "Sin pedidos"}
      />
      <KpiTile
        label="Carga automática"
        value={formatPercent(data.autoPct, 0)}
        hint={`${formatNumber(data.autoCreated)} automáticos · ${formatNumber(
          data.manualCreated,
        )} manuales`}
      />
      <KpiTile
        label="Equipos monitoreados"
        value={formatNumber(data.monitoredDevices)}
        hint="Con al menos un pedido en el período"
      />
      <KpiTile
        label="Insumos distintos"
        value={formatNumber(data.distinctSkus)}
        hint="SKUs pedidos al menos una vez"
      />
    </KpiGrid>
  );
}
