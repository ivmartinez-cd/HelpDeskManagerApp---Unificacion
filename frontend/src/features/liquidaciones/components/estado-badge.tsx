import { Badge, type BadgeVariant } from "@/shared/components/ui/badge";
import type { EstadoLiquidacion } from "../types/liquidaciones";

const ESTADO_CONFIG: Record<EstadoLiquidacion, { variant: BadgeVariant; label: string }> = {
  abierta: { variant: "info", label: "Abierta" },
  preliquidada: { variant: "accent", label: "Preliquidada" },
  recibida: { variant: "neutral", label: "Recibida" },
  observada: { variant: "warning", label: "Observada" },
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
