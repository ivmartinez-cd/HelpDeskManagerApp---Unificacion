import { Badge, type BadgeVariant } from "@/shared/components/ui/badge";
import type { EstadoLiquidacion } from "../types/liquidaciones";

/** Semáforo: amarillo = en trámite, rojo = requiere acción, verde = resuelta. */
const ESTADO_CONFIG: Record<EstadoLiquidacion, { variant: BadgeVariant; label: string }> = {
  abierta: { variant: "warning", label: "Abierta" },
  preliquidada: { variant: "warning", label: "Preliquidada" },
  recibida: { variant: "warning", label: "Recibida" },
  observada: { variant: "danger", label: "Observada" },
  aprobada: { variant: "success", label: "Aprobada" },
  cerrada: { variant: "neutral", label: "Cerrada" },
};

interface EstadoBadgeProps {
  estado: EstadoLiquidacion;
  className?: string;
}

export function EstadoBadge({ estado, className }: EstadoBadgeProps) {
  const { variant, label } = ESTADO_CONFIG[estado];
  return (
    <Badge variant={variant} className={className}>
      {label}
    </Badge>
  );
}
