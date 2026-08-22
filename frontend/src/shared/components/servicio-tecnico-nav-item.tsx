"use client";

import Link from "next/link";
import { ChevronDown, Wrench } from "lucide-react";
import { ServicioTecnicoNavSubmenu } from "@/shared/components/servicio-tecnico-nav-submenu";
import { cn } from "@/shared/utils/cn";

/** Servicio Técnico: grupo hardcodeado (no es módulo), expandible con
 *  los módulos que agrupa — mismo patrón que Prestadores +
 *  Liquidaciones pero en sentido inverso (el padre es el hardcodeado). */
export function ServicioTecnicoNavItem({
  hasSla,
  hasPrestadores,
  hasLiquidaciones,
  hasPreventivos,
  hasAnalisisLogHp,
  isActive,
  submenuOverride,
  onToggleSubmenu,
  onNavigate,
}: {
  hasSla: boolean;
  hasPrestadores: boolean;
  hasLiquidaciones: boolean;
  hasPreventivos: boolean;
  hasAnalisisLogHp: boolean;
  isActive: (route: string) => boolean;
  submenuOverride: boolean | undefined;
  onToggleSubmenu: (expanded: boolean) => void;
  onNavigate: () => void;
}) {
  const stcActive =
    isActive("/servicio-tecnico") ||
    (hasSla && isActive("/sla")) ||
    (hasPrestadores && isActive("/prestadores")) ||
    (hasLiquidaciones && isActive("/liquidaciones")) ||
    (hasPreventivos && isActive("/preventivos")) ||
    (hasAnalisisLogHp && isActive("/analisis-log-hp"));
  const stcHasSubmenu = hasSla || hasPrestadores || hasPreventivos || hasAnalisisLogHp;
  const stcSubmenuExpanded = submenuOverride ?? stcActive;
  const stcHref = hasPrestadores ? "/prestadores" : hasSla ? "/sla" : "/servicio-tecnico";
  return (
    <div className="flex flex-col">
      <div
        className={cn(
          "flex items-center rounded-[8px] transition-colors",
          stcActive
            ? "bg-brand-orange/[0.12] font-semibold text-brand-orange"
            : "text-muted-foreground hover:bg-muted",
        )}
      >
        <Link
          href={stcHref}
          onClick={onNavigate}
          aria-current={stcActive ? "page" : undefined}
          className="flex flex-1 items-center gap-2.5 px-3 py-2.5 font-body text-sm no-underline"
        >
          <Wrench className="h-4 w-4 flex-none" aria-hidden="true" />
          Servicio Técnico
        </Link>
        {stcHasSubmenu && (
          <button
            type="button"
            onClick={() => onToggleSubmenu(!stcSubmenuExpanded)}
            aria-expanded={stcSubmenuExpanded}
            aria-label={
              stcSubmenuExpanded
                ? "Colapsar submenú de Servicio Técnico"
                : "Expandir submenú de Servicio Técnico"
            }
            className="flex-none rounded-[6px] p-2 text-muted-foreground hover:text-foreground"
          >
            <ChevronDown
              className={cn(
                "h-3.5 w-3.5 transition-transform",
                !stcSubmenuExpanded && "-rotate-90",
              )}
            />
          </button>
        )}
      </div>
      {stcHasSubmenu && stcSubmenuExpanded && (
        <ServicioTecnicoNavSubmenu
          hasPrestadores={hasPrestadores}
          hasLiquidaciones={hasLiquidaciones}
          hasSla={hasSla}
          hasPreventivos={hasPreventivos}
          hasAnalisisLogHp={hasAnalisisLogHp}
          onNavigate={onNavigate}
        />
      )}
    </div>
  );
}
