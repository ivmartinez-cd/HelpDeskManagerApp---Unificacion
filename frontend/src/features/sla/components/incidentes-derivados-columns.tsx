import type { IncidenteDerivado } from "../types/derivados";
import type { StatsColumn } from "@/shared/components/ui/stats-table";
import { incidentUrl } from "@/shared/utils/incident-link";

function formatFecha(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export const incidentesDerivadosColumns: StatsColumn<IncidenteDerivado>[] = [
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
  { key: "tecnico", label: "Técnico (PST)", sortField: "tecnico", render: (row) => row.tecnico },
  { key: "operador", label: "Operador", sortField: "operador", render: (row) => row.operador ?? "—" },
  { key: "cliente", label: "Cliente", sortField: "cliente", render: (row) => row.cliente },
  { key: "sucursal", label: "Sucursal", sortField: "sucursal", render: (row) => row.sucursal },
  { key: "modelo", label: "Modelo", sortField: "modelo", render: (row) => row.modelo },
  { key: "nro_serie", label: "N° Serie", sortField: "nro_serie", render: (row) => row.nro_serie },
  {
    key: "fecha_ingreso",
    label: "Ingreso",
    sortField: "fecha_ingreso",
    descFirst: true,
    render: (row) => <span className="tabular-nums">{formatFecha(row.fecha_ingreso)}</span>,
  },
  {
    key: "dias",
    label: "Días",
    sortField: "dias_desde_ingreso",
    descFirst: true,
    align: "right",
    className: "w-20",
    render: (row) => (
      <span
        className={
          row.demorado
            ? "font-semibold text-[#dc2626] dark:text-[#f87171]"
            : "tabular-nums"
        }
      >
        {row.dias_desde_ingreso}
      </span>
    ),
  },
];
