"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  CalendarCheck2,
  CalendarX2,
  ClipboardCheck,
  LayoutDashboard,
  ScrollText,
  Settings,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useSession } from "@/services/session-provider";
import { cn } from "@/shared/utils/cn";

/** Submenú de Vacaciones — mismo lenguaje visual que ContadoresNavSubmenu.
 * Los ítems se filtran por permiso: Aprobaciones requiere `approve` y
 * Gestión Humana muestra su contenido según `manage` (la página es visible
 * con `view` para consultar catálogos). */
interface NavLinkDef {
  href: string;
  label: string;
  icon: LucideIcon;
  visible: boolean;
}

export function VacacionesNavSubmenu({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { user, can } = useSession();
  const esAdmin = user.isSuperadmin || can("vacaciones", "manage");

  const links: NavLinkDef[] = [
    { href: "/vacaciones", label: "Dashboard", icon: LayoutDashboard, visible: true },
    {
      href: "/vacaciones/solicitudes",
      label: "Solicitudes",
      icon: CalendarCheck2,
      visible: esAdmin || can("vacaciones", "create"),
    },
    {
      href: "/vacaciones/aprobaciones",
      label: "Aprobaciones",
      icon: ClipboardCheck,
      visible: esAdmin || can("vacaciones", "approve"),
    },
    {
      href: "/vacaciones/reportes",
      label: "Reportes",
      icon: BarChart3,
      visible: esAdmin,
    },
    {
      href: "/vacaciones/auditoria",
      label: "Auditoría",
      icon: ScrollText,
      visible: esAdmin,
    },
    {
      href: "/vacaciones/configuracion",
      label: "Configuración",
      icon: Settings,
      visible: esAdmin,
    },
    {
      href: "/vacaciones/asistencias",
      label: "Asistencias",
      icon: CalendarX2,
      visible: true,
    },
    {
      href: "/vacaciones/gestion",
      label: "Gestión Humana",
      icon: Users,
      visible: true,
    },
  ];

  return (
    <div className="flex flex-col gap-px py-1.5 pb-2 pl-6 pr-1">
      {links
        .filter((l) => l.visible)
        .map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
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
  );
}
