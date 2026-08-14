"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  CalendarClock,
  ClipboardList,
  FileText,
  Gauge,
  LayoutDashboard,
  Map,
  Settings,
  UserRoundCheck,
  Users,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/shared/utils/cn";

interface NavLinkDef {
  href: string;
  label: string;
  exact: boolean;
  icon: LucideIcon;
}

interface NavSectionDef {
  label: string;
  links: NavLinkDef[];
}

function buildSections({
  hasPrestadores,
  hasLiquidaciones,
  hasSla,
  hasPreventivos,
}: {
  hasPrestadores: boolean;
  hasLiquidaciones: boolean;
  hasSla: boolean;
  hasPreventivos: boolean;
}): NavSectionDef[] {
  const sections: NavSectionDef[] = [];

  if (hasPrestadores) {
    sections.push({
      label: "Prestadores",
      links: [
        { href: "/prestadores", label: "Prestadores Asignados", exact: true, icon: Users },
        { href: "/prestadores/coberturas", label: "Coberturas", exact: false, icon: UserRoundCheck },
      ],
    });
  }

  if (hasLiquidaciones) {
    sections.push(
      {
        label: "Liquidación",
        links: [
          { href: "/liquidaciones", label: "Dashboard", exact: true, icon: LayoutDashboard },
          { href: "/liquidaciones/lista", label: "Liquidaciones", exact: false, icon: FileText },
        ],
      },
      {
        label: "Configuración",
        links: [
          { href: "/liquidaciones/configuracion/prestadores", label: "Prestadores", exact: false, icon: Users },
          { href: "/liquidaciones/configuracion/spsts", label: "SPSTs", exact: false, icon: Settings },
          { href: "/liquidaciones/configuracion/tarifarios", label: "Tarifarios", exact: false, icon: Settings },
          { href: "/liquidaciones/configuracion/tabla-km", label: "Tabla KM", exact: false, icon: Map },
        ],
      },
    );
  }

  if (hasSla) {
    sections.push({
      label: "SLA",
      links: [
        { href: "/sla", label: "SLA", exact: true, icon: Gauge },
        {
          href: "/sla/pendientes-a-cerrar",
          label: "Pendientes a Cerrar",
          exact: false,
          icon: ClipboardList,
        },
      ],
    });
  }

  if (hasPreventivos) {
    sections.push({
      label: "Preventivos",
      links: [
        { href: "/preventivos", label: "Preventivos por zona", exact: false, icon: CalendarClock },
      ],
    });
  }

  return sections;
}

function NavLinkRow({
  link,
  active,
  onNavigate,
}: {
  link: NavLinkDef;
  active: boolean;
  onNavigate?: () => void;
}) {
  const Icon = link.icon;
  return (
    <Link
      href={link.href}
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
      <span className="flex-1 truncate">{link.label}</span>
    </Link>
  );
}

export function ServicioTecnicoNavSubmenu({
  hasPrestadores,
  hasLiquidaciones,
  hasSla,
  hasPreventivos,
  onNavigate,
}: {
  hasPrestadores: boolean;
  hasLiquidaciones: boolean;
  hasSla: boolean;
  hasPreventivos: boolean;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const sections = buildSections({ hasPrestadores, hasLiquidaciones, hasSla, hasPreventivos });

  return (
    <div className="flex flex-col gap-3 py-1.5 pb-2 pl-6 pr-1">
      {sections.map((section) => (
        <div key={section.label} className="flex flex-col gap-px">
          <p className="px-2 pb-1 font-body text-[10px] font-bold uppercase tracking-[.08em] text-muted-foreground/70">
            {section.label}
          </p>
          {section.links.map((link) => {
            const active = link.exact
              ? pathname === link.href
              : pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <NavLinkRow key={link.href} link={link} active={active} onNavigate={onNavigate} />
            );
          })}
        </div>
      ))}
    </div>
  );
}
