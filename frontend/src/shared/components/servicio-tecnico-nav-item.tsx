"use client";

import Link from "next/link";
import { ChevronDown, Wrench } from "lucide-react";
import { useSession } from "@/services/session-provider";
import { ServicioTecnicoNavSubmenu } from "@/shared/components/servicio-tecnico-nav-submenu";
import { canAccessPath } from "@/shared/config/route-permissions";
import { cn } from "@/shared/utils/cn";

/** Servicio Técnico: grupo hardcodeado (no es módulo), expandible con
 *  los módulos que agrupa (sla, prestadores, preventivos, analisis-log-hp,
 *  bono-tecnicos, tareas-varias). Liquidaciones va aparte, como ítem de
 *  nivel superior. */
export function ServicioTecnicoNavItem({
  hasSla,
  hasPrestadores,
  hasPreventivos,
  hasAnalisisLogHp,
  hasBonoTecnicos,
  hasTareasVarias,
  isActive,
  submenuOverride,
  onToggleSubmenu,
  onNavigate,
}: {
  hasSla: boolean;
  hasPrestadores: boolean;
  hasPreventivos: boolean;
  hasAnalisisLogHp: boolean;
  hasBonoTecnicos: boolean;
  hasTareasVarias: boolean;
  isActive: (route: string) => boolean;
  submenuOverride: boolean | undefined;
  onToggleSubmenu: (expanded: boolean) => void;
  onNavigate: () => void;
}) {
  const stcActive =
    isActive("/servicio-tecnico") ||
    (hasSla && isActive("/sla")) ||
    (hasPrestadores && isActive("/prestadores")) ||
    (hasPreventivos && isActive("/preventivos")) ||
    (hasAnalisisLogHp && isActive("/analisis-log-hp")) ||
    (hasBonoTecnicos && isActive("/bono-tecnicos")) ||
    (hasTareasVarias && isActive("/tareas-varias"));
  const stcHasSubmenu =
    hasSla ||
    hasPrestadores ||
    hasPreventivos ||
    hasAnalisisLogHp ||
    hasBonoTecnicos ||
    hasTareasVarias;
  const stcSubmenuExpanded = submenuOverride ?? stcActive;
  const { can, hasFeature } = useSession();
  // El link principal de la fila (no el chevron) tiene que caer en una
  // pantalla real: antes solo contemplaba prestadores/sla y para cualquier
  // otro módulo del grupo (ej. un técnico con solo bono-tecnicos) caía a
  // "/servicio-tecnico", una ruta que no existe ni está mapeada en
  // route-permissions.ts → pantalla de error. Además de tener el módulo,
  // hace falta la acción específica que exige esa ruta (`canAccessPath`) —
  // "bono-tecnicos" con solo `create` (autoservicio) no alcanza para
  // `/bono-tecnicos`, que pide `view` (gerencia).
  const candidatos: [boolean, string][] = [
    [hasPrestadores, "/prestadores"],
    [hasSla, "/sla"],
    [hasPreventivos, "/preventivos"],
    [hasBonoTecnicos, "/bono-tecnicos"],
    [hasTareasVarias, "/tareas-varias"],
    [hasAnalisisLogHp, "/analisis-log-hp"],
  ];
  const stcHref =
    candidatos.find(([tiene, href]) => tiene && canAccessPath(href, { can, hasFeature }))?.[1] ?? "/";
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
          hasSla={hasSla}
          hasPreventivos={hasPreventivos}
          hasAnalisisLogHp={hasAnalisisLogHp}
          hasBonoTecnicos={hasBonoTecnicos}
          hasTareasVarias={hasTareasVarias}
          onNavigate={onNavigate}
        />
      )}
    </div>
  );
}
