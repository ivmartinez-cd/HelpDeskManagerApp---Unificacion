import { EMPTY_VALUE, formatArgDateTime, formatNumber } from "../../utils/format";
import { StatsTable, type StatsColumn } from "./stats-table";
import type { CustomerDetailResponse, DeviceStat, FailureReason, RecentFailure, SkuStat } from "../../types";

/** Los cuatro rankings del detalle de cliente. Salen armados y ordenados del
 * backend (`topSkus`, `topDevices`, `failureReasons`, `recentFailures`); acá
 * se formatean y cada encabezado reordena lo recibido. */

const skuColumns: StatsColumn<SkuStat>[] = [
  { key: "sku", label: "SKU", sortField: "sku", render: (row) => <span className="font-semibold">{row.sku}</span> },
  {
    key: "description",
    label: "Descripción",
    sortField: "description",
    render: (row) => <span className="text-muted-foreground">{row.description || EMPTY_VALUE}</span>,
  },
  { key: "count", label: "Pedidos", align: "right", sortField: "count", descFirst: true, render: (row) => formatNumber(row.count) },
];

const deviceColumns: StatsColumn<DeviceStat>[] = [
  {
    key: "serial",
    label: "N° de serie",
    sortField: "deviceSerial",
    render: (row) => <span className="font-semibold">{row.deviceSerial}</span>,
  },
  { key: "count", label: "Pedidos", align: "right", sortField: "count", descFirst: true, render: (row) => formatNumber(row.count) },
];

const failureReasonColumns: StatsColumn<FailureReason>[] = [
  { key: "reason", label: "Motivo", sortField: "reason", render: (row) => row.reason },
  { key: "count", label: "Veces", align: "right", sortField: "count", descFirst: true, render: (row) => formatNumber(row.count) },
  {
    key: "lastAt",
    label: "Último",
    sortField: "lastAt",
    descFirst: true,
    align: "right",
    render: (row) => (
      <span className="text-muted-foreground">{formatArgDateTime(row.lastAt)}</span>
    ),
  },
];

const recentFailureColumns: StatsColumn<RecentFailure>[] = [
  {
    key: "createdAt",
    label: "Fecha",
    sortField: "createdAt",
    descFirst: true,
    render: (row) => <span className="whitespace-nowrap">{formatArgDateTime(row.createdAt)}</span>,
  },
  { key: "sku", label: "SKU", sortField: "sku", render: (row) => row.sku || EMPTY_VALUE },
  { key: "serial", label: "Equipo", sortField: "deviceSerial", render: (row) => row.deviceSerial || EMPTY_VALUE },
  {
    key: "detail",
    label: "Detalle",
    sortField: "detail",
    render: (row) => <span className="text-muted-foreground">{row.detail || EMPTY_VALUE}</span>,
  },
];

export function TablasCliente({ data }: { data: CustomerDetailResponse }) {
  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-6 xl:grid-cols-2">
        <StatsTable
          title="Insumos más pedidos"
          subtitle="Top de SKUs del período"
          columns={skuColumns}
          rows={data.topSkus}
          rowKey={(row) => row.sku}
        />
        <StatsTable
          title="Equipos con más pedidos"
          subtitle="Top de series del período"
          columns={deviceColumns}
          rows={data.topDevices}
          rowKey={(row) => row.deviceSerial}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <StatsTable
          title="Motivos de fallo"
          subtitle="Pedidos que no se pudieron cargar en Canal Directo"
          columns={failureReasonColumns}
          rows={data.failureReasons}
          rowKey={(row) => row.reason}
          emptyLabel="Sin fallos en el período seleccionado."
        />
        <StatsTable
          title="Fallos recientes"
          subtitle="Los últimos casos, más nuevo primero"
          columns={recentFailureColumns}
          rows={data.recentFailures}
          rowKey={(row, index) => `${row.createdAt}-${row.sku ?? ""}-${index}`}
          emptyLabel="Sin fallos en el período seleccionado."
        />
      </div>
    </div>
  );
}
