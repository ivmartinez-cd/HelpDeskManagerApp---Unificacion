import type { BadgeVariant } from "@/shared/components/ui/badge";
import type { EstadoAlerta } from "../types/liquidaciones";

/** Estilos y transiciones de estado de alertas — compartidos entre la sección
 * Alertas y las sub-filas de la tabla de incidentes. */
export const CODIGO_ALT009 = "ALT009";

export const ESTADO_ALERTA_STYLES: Record<EstadoAlerta, { variant: BadgeVariant; label: string }> = {
  pendiente: { variant: "warning", label: "Pendiente" },
  en_revision: { variant: "info", label: "En revisión" },
  resuelta: { variant: "success", label: "Resuelta" },
  descartada: { variant: "neutral", label: "Descartada" },
};

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
