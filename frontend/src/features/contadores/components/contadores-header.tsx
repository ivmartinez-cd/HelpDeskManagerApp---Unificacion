import Link from "next/link";
import {
  Calculator,
  ChartColumn,
  Database,
  FileSpreadsheet,
  FolderSync,
  Printer,
  Radio,
  Sigma,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/shared/utils/cn";

export type ToolKey =
  | "proyeccion"
  | "calc"
  | "db3"
  | "en0"
  | "suma-fija"
  | "ftp"
  | "sds"
  | "ers";

interface ToolDef {
  key: ToolKey;
  label: string;
  icon: LucideIcon;
  description: string;
}

export const TOOLS: ToolDef[] = [
  {
    key: "proyeccion",
    label: "Proyección",
    icon: ChartColumn,
    description: "Proyecta lecturas de contadores y genera archivos para SiGes.",
  },
  {
    key: "calc",
    label: "Calculadora",
    icon: Calculator,
    description: "Calcula estimaciones manuales de lectura y consumo diario.",
  },
  {
    key: "db3",
    label: "DB3 a CSV",
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
    icon: FolderSync,
    description: "Gestión de servidores FTP de clientes y descarga automática de DB3.",
  },
  {
    key: "sds",
    label: "HP SDS",
    icon: Printer,
    description: "Integración con HP SDS LATAM para lectura de contadores.",
  },
  {
    key: "ers",
    label: "Epson ERS",
    icon: Radio,
    description: "Integración con Epson Remote Services (ERS) para telemetría.",
  },
];

interface Props {
  activeTool: ToolKey;
}

export function ContadoresHeader({ activeTool }: Props) {
  const currentDef = TOOLS.find((t) => t.key === activeTool) ?? TOOLS[0];

  return (
    <div className="relative overflow-hidden border-b border-black/10 dark:border-white/10 bg-card/60 backdrop-blur">
      <div className="pointer-events-none absolute -top-24 -right-24 h-64 w-64 rounded-full bg-accent/10 blur-3xl" />

      <div className="relative mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <h1 className="text-2xl font-black uppercase tracking-tighter text-foreground sm:text-3xl">
          Módulo de Contadores
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">{currentDef.description}</p>

        <nav
          aria-label="Herramientas de contadores"
          className="mt-6 flex space-x-1 overflow-x-auto rounded-2xl border border-black/10 dark:border-white/10 bg-muted/60 p-1.5 thin-scrollbar"
        >
          {TOOLS.map((tool) => {
            const Icon = tool.icon;
            const isSelected = activeTool === tool.key;
            return (
              <Link
                key={tool.key}
                href={`/contadores?tool=${tool.key}`}
                aria-current={isSelected ? "page" : undefined}
                className={cn(
                  "flex shrink-0 items-center gap-2 whitespace-nowrap rounded-xl px-3.5 py-2 text-xs font-semibold transition-all duration-150",
                  isSelected
                    ? "bg-accent text-accent-foreground shadow-md shadow-accent/25"
                    : "text-muted-foreground hover:bg-background/60 hover:text-foreground",
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{tool.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
