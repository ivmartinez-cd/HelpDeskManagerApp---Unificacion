import { AlertTriangle, Ban, CheckCircle2, Search, type LucideIcon } from "lucide-react";
import type { BadgeVariant } from "@/shared/components/ui/badge";
import type { Alerta, EstadoAlerta } from "../types/liquidaciones";

/** Estilos y transiciones de estado de alertas — compartidos entre la sección
 * Alertas y las sub-filas de la tabla de incidentes. */
export const CODIGO_ALT009 = "ALT009";

export const ESTADO_ALERTA_STYLES: Record<EstadoAlerta, { variant: BadgeVariant; label: string }> = {
  pendiente: { variant: "warning", label: "Pendiente" },
  en_revision: { variant: "info", label: "En revisión" },
  resuelta: { variant: "success", label: "Resuelta" },
  descartada: { variant: "neutral", label: "Descartada" },
};

/** Tono redundante al color de cada estado (ícono + fondo/borde de la fila),
 * para que la severidad no dependa solo de distinguir el matiz — acordado
 * con Iván sobre mockup de variantes, 2026-09-08. No reemplaza
 * `ESTADO_ALERTA_STYLES` (label/variant del Badge genérico), lo complementa. */
export const ESTADO_ALERTA_TONO: Record<
  EstadoAlerta,
  { icon: LucideIcon; rowBorder: string; rowBg: string; pillBg: string; pillText: string }
> = {
  pendiente: {
    icon: AlertTriangle,
    rowBorder: "border-l-warning",
    rowBg: "bg-warning/[0.08]",
    pillBg: "bg-warning/15",
    pillText: "text-warning",
  },
  en_revision: {
    icon: Search,
    rowBorder: "border-l-info",
    rowBg: "bg-info/[0.08]",
    pillBg: "bg-info/15",
    pillText: "text-info",
  },
  resuelta: {
    icon: CheckCircle2,
    rowBorder: "border-l-success",
    rowBg: "bg-success/[0.08]",
    pillBg: "bg-success/15",
    pillText: "text-success",
  },
  descartada: {
    icon: Ban,
    rowBorder: "border-l-muted-foreground",
    rowBg: "bg-muted/[0.08]",
    pillBg: "bg-muted/50",
    pillText: "text-muted-foreground",
  },
};

/** Peor estado ACTIVO (pendiente pesa más que en_revisión) entre las alertas
 * de un incidente — define el tono de su fila colapsada, antes de abrirla
 * con la flecha. `null` si no hay ninguna activa (todas resueltas/
 * descartadas), igual que `estado_validacion === "ok"` en el backend
 * (`triage_alertas.py`). */
export function peorTonoActivo(alertas: Alerta[]) {
  if (alertas.some((a) => a.estado === "pendiente")) return ESTADO_ALERTA_TONO.pendiente;
  if (alertas.some((a) => a.estado === "en_revision")) return ESTADO_ALERTA_TONO.en_revision;
  return null;
}

/** "Descartar" pide justificación (el backend la exige); el resto es directo. */
export const TRANSICIONES_ALERTA: Record<
  EstadoAlerta,
  { estado: EstadoAlerta; label: string; pideJustificacion?: boolean }[]
> = {
  pendiente: [
    { estado: "en_revision", label: "Revisar" },
    { estado: "resuelta", label: "Resolver" },
    { estado: "descartada", label: "Descartar", pideJustificacion: true },
  ],
  en_revision: [
    { estado: "resuelta", label: "Resolver" },
    { estado: "descartada", label: "Descartar", pideJustificacion: true },
  ],
  resuelta: [{ estado: "en_revision", label: "Reabrir" }],
  descartada: [{ estado: "en_revision", label: "Reabrir" }],
};
