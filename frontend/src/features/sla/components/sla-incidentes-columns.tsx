import type { IncidenteVencido } from "../types/sla";
import type { StatsColumn } from "@/shared/components/ui/stats-table";
import { incidentUrl } from "@/shared/utils/incident-link";

function formatFecha(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export const incidenteColumns: StatsColumn<IncidenteVencido>[] = [
  {
    key: "id",
    label: "ID",
    sortField: "id_incidente",
    className: "w-20",
    render: (row) => (
      <a
        href={incidentUrl(row.id_incidente)}
        target="_blank"
        rel="noopener noreferrer"
        className="font-semibold tabular-nums text-brand-orange hover:underline"
      >
        {row.id_incidente}
      </a>
    ),
  },
  { key: "tecnico", label: "Técnico", sortField: "tecnico", render: (row) => row.tecnico },
  { key: "region", label: "Región", sortField: "region", render: (row) => row.region },
  { key: "cliente", label: "Cliente", sortField: "cliente", render: (row) => row.cliente },
  { key: "sucursal", label: "Sucursal", sortField: "sucursal", render: (row) => row.sucursal },
  { key: "modelo", label: "Modelo", sortField: "modelo", render: (row) => row.modelo },
  {
    key: "fecha_operativo",
    label: "Operativo",
    sortField: "fecha_operativo",
    descFirst: true,
    render: (row) => (
      <span className="tabular-nums">{formatFecha(row.fecha_operativo)}</span>
    ),
  },
  { key: "rango", label: "Rango", sortField: "rango", render: (row) => row.rango },
  {
    key: "sla_horas",
    label: "SLA (h)",
    sortField: "sla_horas",
    descFirst: true,
    align: "right",
    className: "w-20",
    render: (row) => row.sla_horas,
  },
  {
    key: "horas_vencido",
    label: "Vencido (h)",
    sortField: "horas_vencido",
    descFirst: true,
    align: "right",
    className: "w-28",
    render: (row) => (
      <span className="font-semibold text-[#dc2626] dark:text-[#f87171]">
        {row.horas_vencido}
      </span>
    ),
  },
];
