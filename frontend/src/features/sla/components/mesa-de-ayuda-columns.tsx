import type { IncidenteMesaAyuda } from "../types/mesa-ayuda";
import type { StatsColumn } from "@/shared/components/ui/stats-table";
import { incidentUrl } from "@/shared/utils/incident-link";
import { AvisoCasoSucursal } from "./aviso-caso-sucursal";

function formatFecha(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

/** Otro caso de la misma sucursal ya derivado a un técnico: si nadie
 *  coordina, el técnico viaja sin enterarse del caso de MDA. */
function VisitaEnSucursal({ row }: { row: IncidenteMesaAyuda }) {
  if (row.visita_id_incidente === null) return <span className="text-muted-foreground">—</span>;
  return (
    <span className="flex flex-col gap-0.5">
      <AvisoCasoSucursal id={row.visita_id_incidente} total={row.visitas_en_sucursal} />
      <span className="text-xs text-muted-foreground">
        {row.visita_tecnico} · {row.visita_estado}
      </span>
    </span>
  );
}

export const mesaDeAyudaColumns: StatsColumn<IncidenteMesaAyuda>[] = [
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
  { key: "operador", label: "Operador (últ. modif.)", sortField: "operador", render: (row) => row.operador },
  { key: "cliente", label: "Cliente", sortField: "cliente", render: (row) => row.cliente },
  { key: "sucursal", label: "Sucursal", sortField: "sucursal", render: (row) => row.sucursal },
  {
    key: "visita",
    label: "Visita en sucursal",
    sortField: "visita_id_incidente",
    render: (row) => <VisitaEnSucursal row={row} />,
  },
  { key: "modelo", label: "Modelo", sortField: "modelo", render: (row) => row.modelo },
  { key: "nro_serie", label: "N° Serie", sortField: "nro_serie", render: (row) => row.nro_serie },
  { key: "tipo", label: "Tipo", sortField: "tipo", render: (row) => row.tipo },
  { key: "estado", label: "Estado", sortField: "estado", render: (row) => row.estado },
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
    sortField: "dias_transcurridos",
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
        {row.dias_transcurridos}
      </span>
    ),
  },
];
