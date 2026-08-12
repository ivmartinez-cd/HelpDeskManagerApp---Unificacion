import { cn } from "@/shared/utils/cn";
import type { EstadoLiquidacion } from "../types/liquidaciones";

const LABELS: Record<EstadoLiquidacion, string> = {
  abierta: "Abierta",
  recibida: "Recibida",
  aprobada: "Aprobada",
  cerrada: "Cerrada",
};

interface EstadoBadgeProps {
  estado: EstadoLiquidacion;
  className?: string;
}

export function EstadoBadge({ estado, className }: EstadoBadgeProps) {
  return (
    <span
      className={cn(
        "font-body text-sm",
        estado === "aprobada" &&
          "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
        estado === "cerrada" &&
          "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
        className,
      )}
      style={
        estado === "aprobada"
          ? { background: "rgba(34,197,94,.15)", color: "#4ade80" }
          : estado === "cerrada"
            ? { background: "rgba(255,255,255,.1)", color: "rgba(255,255,255,.5)" }
            : { color: "rgba(255,255,255,.6)" }
      }
    >
      {LABELS[estado]}
    </span>
  );
}
