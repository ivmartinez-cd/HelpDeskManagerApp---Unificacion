"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import {
  BarChart3,
  Briefcase,
  Building2,
  CalendarCheck2,
  CalendarX2,
  ClipboardCheck,
  LayoutDashboard,
  PartyPopper,
  ScrollText,
  Settings,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useSession } from "@/services/session-provider";
import { canAccessPath } from "@/shared/config/route-permissions";
import { cn } from "@/shared/utils/cn";

/** Submenú de Gestión de Personal (module key `vacaciones`) — mismo lenguaje
 * visual que ContadoresNavSubmenu, con títulos de sección del handoff
 * (Vacaciones / Asistencias / Gestión Humana / Configuración). Los ítems se
 * filtran por permiso según el mapa central ruta → permiso (ADR-029,
 * `shared/config/route-permissions.ts`): Solicitudes pide `create` o `manage`,
 * Aprobaciones `approve` o `manage`, Reportes/Auditoría/Configuración `manage`;
 * Gestión Humana es visible con `view` (la página muestra su contenido según
 * `manage`, para consultar catálogos). Gestión Humana son 4 accesos directos
 * (Empleados/Sectores/Cargos/Feriados) sobre la misma ruta `/vacaciones/gestion`
 * con `?tab=`, como en el handoff (07-Gestion-Humana) — antes era un solo
 * link a "Personal" que siempre abría en Empleados, y Feriados quedaba sin
 * acceso directo. */
interface NavLinkDef {
  href: string;
  label: string;
  icon: LucideIcon;
  visible: boolean;
  /** Override de `pathname === href` para links que comparten ruta y se
   * distinguen por query param (ej. Gestión Humana con `?tab=`). */
  active?: boolean;
}

interface NavGroupDef {
  titulo: string;
  items: NavLinkDef[];
}

export function VacacionesNavSubmenu({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { can, hasFeature } = useSession();
  const puedeAbrir = (href: string) => canAccessPath(href, { can, hasFeature });
  const enGestion = pathname === "/vacaciones/gestion";
  const tabGestion = enGestion ? (searchParams.get("tab") ?? "empleados") : null;

  const grupos: NavGroupDef[] = [
    {
      titulo: "Vacaciones",
      items: [
        {
          href: "/vacaciones",
          label: "Dashboard",
          icon: LayoutDashboard,
          visible: puedeAbrir("/vacaciones"),
        },
        {
          href: "/vacaciones/solicitudes",
          label: "Solicitudes",
          icon: CalendarCheck2,
          visible: puedeAbrir("/vacaciones/solicitudes"),
        },
        {
          href: "/vacaciones/aprobaciones",
          label: "Aprobaciones",
          icon: ClipboardCheck,
          visible: puedeAbrir("/vacaciones/aprobaciones"),
        },
        {
          href: "/vacaciones/reportes",
          label: "Reportes",
          icon: BarChart3,
          visible: puedeAbrir("/vacaciones/reportes"),
        },
      ],
    },
    {
      titulo: "Asistencias",
      items: [
        {
          href: "/vacaciones/asistencias",
          label: "Registro de asistencias",
          icon: CalendarX2,
          visible: puedeAbrir("/vacaciones/asistencias"),
        },
      ],
    },
    {
      titulo: "Gestión Humana",
      items: [
        {
          href: "/vacaciones/gestion",
          label: "Empleados",
          icon: Users,
          visible: puedeAbrir("/vacaciones/gestion"),
          active: tabGestion === "empleados",
        },
        {
          href: "/vacaciones/gestion?tab=sectores",
          label: "Sectores",
          icon: Building2,
          visible: puedeAbrir("/vacaciones/gestion"),
          active: tabGestion === "sectores",
        },
        {
          href: "/vacaciones/gestion?tab=cargos",
          label: "Cargos",
          icon: Briefcase,
          visible: puedeAbrir("/vacaciones/gestion"),
          active: tabGestion === "cargos",
        },
        {
          href: "/vacaciones/gestion?tab=feriados",
          label: "Feriados",
          icon: PartyPopper,
          visible: puedeAbrir("/vacaciones/gestion"),
          active: tabGestion === "feriados",
        },
      ],
    },
    {
      titulo: "Configuración",
      items: [
        {
          href: "/vacaciones/auditoria",
          label: "Auditoría",
          icon: ScrollText,
          visible: puedeAbrir("/vacaciones/auditoria"),
        },
        {
          href: "/vacaciones/configuracion",
          label: "Configuración",
          icon: Settings,
          visible: puedeAbrir("/vacaciones/configuracion"),
        },
      ],
    },
  ];

  const visibles = grupos
    .map((g) => ({ ...g, items: g.items.filter((i) => i.visible) }))
    .filter((g) => g.items.length > 0);

  return (
    <div className="flex flex-col py-1.5 pb-2 pl-4 pr-1">
      {visibles.map((grupo, idx) => (
        <div key={grupo.titulo} className="flex flex-col gap-px">
          {idx > 0 && <div className="mx-2 mb-1.5 mt-2 h-px bg-border/70" />}
          <p className="px-2 pb-1 font-heading text-[9.5px] font-bold uppercase tracking-[.09em] text-muted-foreground/80">
            {grupo.titulo}
          </p>
          {grupo.items.map(({ href, label, icon: Icon, active: activeOverride }) => {
            const active = activeOverride ?? pathname === href;
            return (
              <Link
                key={href}
                href={href}
                onClick={onNavigate}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-2 rounded-[6px] px-2 py-1.5 font-body text-[13px] no-underline transition-colors",
                  active
                    ? "bg-brand-orange/[0.12] font-bold text-brand-orange"
                    : "text-brand-orange/85 hover:bg-muted hover:text-brand-orange",
                )}
              >
                <Icon className="h-3.5 w-3.5 flex-none" aria-hidden="true" />
                <span className="flex-1 truncate">{label}</span>
              </Link>
            );
          })}
        </div>
      ))}
    </div>
  );
}
