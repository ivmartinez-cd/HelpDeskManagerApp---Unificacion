import {
  ChartColumn,
  Database,
  FileSpreadsheet,
  FolderSync,
  Printer,
  Radio,
  Sigma,
  type LucideIcon,
} from "lucide-react";

export type ToolKey = "proyeccion" | "db3" | "en0" | "suma-fija" | "ftp" | "sds" | "ers";

export interface ToolDef {
  key: ToolKey;
  label: string;
  /** Rótulo orientado a la acción, usado en las cards del hub y en los
   * modales (ej. "Descargar SDS" en vez de "HP SDS"). Si falta, se usa
   * `label`. */
  navLabel?: string;
  icon: LucideIcon;
  description: string;
  /** La card queda visible en el hub pero sin lógica detrás (sin backend,
   * sin modal funcional) — usado para Proyección, cuya lógica se dio de
   * baja a propósito sin sacar la card del catálogo. */
  disabled?: boolean;
}

/** Catálogo único de las 7 herramientas de Contadores — fuente de verdad
 * para el hub "Centro de Contadores" y para tool-launcher-modal.tsx. */
export const TOOLS: ToolDef[] = [
  {
    key: "proyeccion",
    label: "Proyección",
    navLabel: "Proyección Contadores",
    icon: ChartColumn,
    description: "Proyecta lecturas de contadores y genera archivos para SiGes.",
    disabled: true,
  },
  {
    key: "db3",
    label: "DB3 a CSV",
    navLabel: "Procesar DB3",
    icon: Database,
    description: "Consolida bases de datos SQLite (.db3) de impresoras a CSV.",
  },
  {
    key: "en0",
    label: "Estimación en 0",
    icon: FileSpreadsheet,
    description: "Procesa planillas de Falta Contador asignando categorías.",
  },
  {
    key: "suma-fija",
    label: "Suma Fija",
    icon: Sigma,
    description: "Calcula lecturas fijas sumando hojas según el estado del equipo.",
  },
  {
    key: "ftp",
    label: "Clientes FTP",
    navLabel: "Descarga FTP",
    icon: FolderSync,
    description: "Gestión de servidores FTP de clientes y descarga automática de DB3.",
  },
  {
    key: "sds",
    label: "HP SDS",
    navLabel: "Descargar SDS",
    icon: Printer,
    description: "Integración con HP SDS LATAM para lectura de contadores.",
  },
  {
    key: "ers",
    label: "Epson ERS",
    navLabel: "Descargar ERS",
    icon: Radio,
    description: "Integración con Epson Remote Services (ERS) para telemetría.",
  },
];
