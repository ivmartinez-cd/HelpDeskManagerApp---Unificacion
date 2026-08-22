"use client";

import Link from "next/link";
import {
  BarChart2,
  ChevronDown,
  Circle,
  Clock,
  FileSearch,
  Package,
  Settings,
  UserRound,
  type LucideIcon,
  MessageCircle,
} from "lucide-react";
import type { ModuleSummary } from "@/features/auth/api/auth-api";
import { ContadoresNavSubmenu } from "@/shared/components/contadores-nav-submenu";
import { InsumosNavSubmenu } from "@/shared/components/insumos-nav-submenu";
import { VacacionesNavSubmenu } from "@/shared/components/vacaciones-nav-submenu";
import { cn } from "@/shared/utils/cn";

const MODULE_ICONS: Record<string, LucideIcon> = {
  contadores: BarChart2,
  insumos: Package,
  vacaciones: UserRound,
  turnos: Clock,
  "analisis-log-hp": FileSearch,
  wati: MessageCircle,
  admin: Settings,
};

export function ModuleNavItem({
  module,
  href,
  active,
  submenuOverride,
  onToggleSubmenu,
  onNavigate,
}: {
  module: ModuleSummary;
  href: string;
  active: boolean;
  submenuOverride: boolean | undefined;
  onToggleSubmenu: (expanded: boolean) => void;
  onNavigate: () => void;
}) {
  const isContadores = module.key === "contadores";
  const isInsumos = module.key === "insumos";
  const isVacaciones = module.key === "vacaciones";
  const hasSubmenu = isContadores || isInsumos || isVacaciones;
  const submenuExpanded = submenuOverride ?? active;
  const ModuleIcon = MODULE_ICONS[module.key] ?? Circle;
  return (
    <div className="flex flex-col">
      <div
        className={cn(
          "flex items-center rounded-[8px] transition-colors",
          active
            ? "bg-brand-orange/[0.12] font-semibold text-brand-orange"
            : "text-muted-foreground hover:bg-muted",
        )}
      >
        <Link
          href={href}
          onClick={onNavigate}
          aria-current={active ? "page" : undefined}
          className="flex flex-1 items-center gap-2.5 px-3 py-2.5 font-body text-sm no-underline"
        >
          <ModuleIcon className="h-4 w-4 flex-none" aria-hidden="true" />
          {module.label}
        </Link>
        {hasSubmenu && (
          <button
            type="button"
            onClick={() => onToggleSubmenu(!submenuExpanded)}
            aria-expanded={submenuExpanded}
            aria-label={
              submenuExpanded
                ? `Colapsar submenú de ${module.label}`
                : `Expandir submenú de ${module.label}`
            }
            className="flex-none rounded-[6px] p-2 text-muted-foreground hover:text-foreground"
          >
            <ChevronDown
              className={cn(
                "h-3.5 w-3.5 transition-transform",
                !submenuExpanded && "-rotate-90",
              )}
            />
          </button>
        )}
      </div>
      {isContadores && submenuExpanded && <ContadoresNavSubmenu onNavigate={onNavigate} />}
      {isInsumos && submenuExpanded && <InsumosNavSubmenu onNavigate={onNavigate} />}
      {isVacaciones && submenuExpanded && <VacacionesNavSubmenu onNavigate={onNavigate} />}
    </div>
  );
}
