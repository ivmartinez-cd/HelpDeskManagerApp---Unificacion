import type { IncidenteMesaAyuda } from "../types/mesa-ayuda";
import type { StatsColumn } from "@/shared/components/ui/stats-table";
import { incidentUrl } from "@/shared/utils/incident-link";

function formatFecha(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export const mesaDeAyudaColumns: StatsColumn<IncidenteMesaAyuda>[] = [
  {
    key: "id",
    label: "ID",
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
  { key: "operador", label: "Operador (últ. modif.)", render: (row) => row.operador },
  { key: "cliente", label: "Cliente", render: (row) => row.cliente },
  { key: "sucursal", label: "Sucursal", render: (row) => row.sucursal },
  { key: "modelo", label: "Modelo", render: (row) => row.modelo },
  { key: "nro_serie", label: "N° Serie", render: (row) => row.nro_serie },
  { key: "tipo", label: "Tipo", render: (row) => row.tipo },
  { key: "estado", label: "Estado", render: (row) => row.estado },
  {
    key: "fecha_ingreso",
    label: "Ingreso",
    render: (row) => <span className="tabular-nums">{formatFecha(row.fecha_ingreso)}</span>,
  },
  {
    key: "dias",
    label: "Días",
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
        {row.dias_transcurridos}
      </span>
    ),
  },
];
