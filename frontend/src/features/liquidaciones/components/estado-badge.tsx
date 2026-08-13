import { Badge } from "@/shared/components/ui/badge";
import { cn } from "@/shared/utils/cn";
import type { EstadoLiquidacion } from "../types/liquidaciones";

const LABELS: Record<EstadoLiquidacion, string> = {
  abierta: "Abierta",
  preliquidada: "Preliquidada",
  recibida: "Recibida",
  observada: "Observada",
  aprobada: "Aprobada",
  cerrada: "Cerrada",
};

interface EstadoBadgeProps {
  estado: EstadoLiquidacion;
  className?: string;
}

export function EstadoBadge({ estado, className }: EstadoBadgeProps) {
  if (estado === "aprobada") {
    return (
      <Badge variant="success" className={className}>
        {LABELS[estado]}
      </Badge>
    );
  }
  if (estado === "observada") {
    return (
      <Badge variant="warning" className={className}>
        {LABELS[estado]}
      </Badge>
    );
  }
  if (estado === "cerrada") {
    return (
      <Badge variant="neutral" className={className}>
        {LABELS[estado]}
      </Badge>
    );
  }
  return (
    <span className={cn("font-body text-sm text-muted-foreground", className)}>
      {LABELS[estado]}
    </span>
  );
}
