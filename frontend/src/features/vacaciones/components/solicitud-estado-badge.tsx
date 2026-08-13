import type { EstadoSolicitud } from "../types/vacaciones";

const ESTILOS: Record<EstadoSolicitud, string> = {
  PENDING: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  APPROVED: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
  REJECTED: "bg-red-500/15 text-red-600 dark:text-red-400",
};

const LABELS: Record<EstadoSolicitud, string> = {
  PENDING: "Pendiente",
  APPROVED: "Aprobada",
  REJECTED: "Rechazada",
};

export function SolicitudEstadoBadge({ estado }: { estado: EstadoSolicitud }) {
  return (
    <span
      className={`inline-block rounded-[20px] px-2.5 py-1 font-body text-xs font-semibold ${ESTILOS[estado]}`}
    >
      {LABELS[estado]}
    </span>
  );
}
