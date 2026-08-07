"use client";

import {
  BarChart3,
  Calculator,
  Database,
  FileSpreadsheet,
  FileSpreadsheetIcon,
  FolderSync,
  Printer,
  Radio,
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
  shortLabel: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

export const TOOLS: ToolDef[] = [
  {
    key: "proyeccion",
    label: "Proyección",
    shortLabel: "Proyección",
    icon: BarChart3,
    description: "Proyecta lecturas de contadores y genera archivos para SiGes.",
  },
  {
    key: "calc",
    label: "Calculadora",
    shortLabel: "Calculadora",
    icon: Calculator,
    description: "Calcula estimaciones manuales de lectura y consumo diario.",
  },
  {
    key: "db3",
    label: "DB3 a CSV",
    shortLabel: "DB3 -> CSV",
    icon: Database,
    description: "Consolida bases de datos SQLite (.db3) de impresoras a CSV.",
  },
  {
    key: "en0",
    label: "Estimación en 0",
    shortLabel: "Estimación 0",
    icon: FileSpreadsheet,
    description: "Procesa planillas de Falta Contador asignando categorías.",
  },
  {
    key: "suma-fija",
    label: "Suma Fija",
    shortLabel: "Suma Fija",
    icon: FileSpreadsheetIcon,
    description: "Calcula lecturas fijas sumando hojas según el estado del equipo.",
  },
  {
    key: "ftp",
    label: "Clientes FTP",
    shortLabel: "FTP",
    icon: FolderSync,
    description: "Gestión de servidores FTP de clientes y descarga automática de DB3.",
  },
  {
    key: "sds",
    label: "HP SDS",
    shortLabel: "HP SDS",
    icon: Printer,
    description: "Integración con HP SDS LATAM para lectura de contadores.",
  },
  {
    key: "ers",
    label: "Epson ERS",
    shortLabel: "Epson ERS",
    icon: Radio,
    description: "Integración con Epson Remote Services (ERS) para telemetría.",
  },
];

interface Props {
  activeTool: ToolKey;
  onSelectTool: (key: ToolKey) => void;
}

export function ContadoresHeader({ activeTool, onSelectTool }: Props) {
  const currentDef = TOOLS.find((t) => t.key === activeTool) ?? TOOLS[0];

  return (
    <div className="border-b border-border bg-card/60 backdrop-blur">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              Módulo de Contadores
            </h1>
            <p className="text-sm text-muted-foreground mt-1">{currentDef.description}</p>
          </div>
        </div>

        {/* Tabs de herramientas */}
        <div className="mt-6 flex overflow-x-auto thin-scrollbar space-x-1 rounded-2xl bg-muted/60 p-1.5 border border-border/50">
          {TOOLS.map((tool) => {
            const Icon = tool.icon;
            const isSelected = activeTool === tool.key;
            return (
              <button
                key={tool.key}
                onClick={() => onSelectTool(tool.key)}
                className={cn(
                  "flex items-center gap-2 whitespace-nowrap rounded-xl px-3.5 py-2 text-xs font-semibold transition-all duration-150 shrink-0",
                  isSelected
                    ? "bg-primary text-primary-foreground shadow-md shadow-primary/25"
                    : "text-muted-foreground hover:bg-background/60 hover:text-foreground",
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{tool.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
