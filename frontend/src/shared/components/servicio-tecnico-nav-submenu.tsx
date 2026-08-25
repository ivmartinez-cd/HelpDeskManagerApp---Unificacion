"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Award,
  CalendarClock,
  ClipboardList,
  DollarSign,
  FileSearch,
  FileText,
  Gauge,
  Headset,
  LayoutDashboard,
  Map,
  ScrollText,
  UserRoundCheck,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useSession } from "@/services/session-provider";
import { canAccessPath } from "@/shared/config/route-permissions";
import { cn } from "@/shared/utils/cn";

interface NavLinkDef {
  href: string;
  label: string;
  exact: boolean;
  icon: LucideIcon;
}

interface NavSectionDef {
  label: string | null;
  links: NavLinkDef[];
}

function buildSections({
  hasPrestadores,
  hasLiquidaciones,
  hasSla,
  hasPreventivos,
  hasAnalisisLogHp,
  hasBonoTecnicos,
  bonoTecnicosHref,
}: {
  hasPrestadores: boolean;
  hasLiquidaciones: boolean;
  hasSla: boolean;
  hasPreventivos: boolean;
  hasAnalisisLogHp: boolean;
  hasBonoTecnicos: boolean;
  bonoTecnicosHref: string;
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
          { href: "/liquidaciones", label: "Resumen", exact: true, icon: LayoutDashboard },
          { href: "/liquidaciones/lista", label: "Liquidaciones", exact: false, icon: FileText },
        ],
      },
      {
        label: "Configuración",
        links: [
          { href: "/liquidaciones/configuracion/prestadores", label: "Conf. Prestadores", exact: false, icon: Users },
          { href: "/liquidaciones/configuracion/spsts", label: "SPSTs", exact: false, icon: ScrollText },
          { href: "/liquidaciones/configuracion/tarifarios", label: "Tarifarios", exact: false, icon: DollarSign },
          { href: "/liquidaciones/configuracion/tabla-km", label: "Tabla KM", exact: false, icon: Map },
          { href: "/liquidaciones/configuracion/reglas", label: "Reglas de alerta", exact: false, icon: ScrollText },
        ],
      },
    );
  }

  if (hasSla) {
    sections.push({
      label: "SLA",
      links: [
        { href: "/sla", label: "Resumen SLA", exact: true, icon: Gauge },
        {
          href: "/sla/pendientes-a-cerrar",
          label: "Pendientes a Cerrar",
          exact: false,
          icon: ClipboardList,
        },
        {
          href: "/sla/mesa-de-ayuda",
          label: "Incidentes Mesa de Ayuda",
          exact: false,
          icon: Headset,
        },
      ],
    });
  }

  if (hasPreventivos) {
    sections.push({
      label: null,
      links: [
        { href: "/preventivos", label: "Preventivos por zona", exact: false, icon: CalendarClock },
      ],
    });
  }

  if (hasAnalisisLogHp) {
    sections.push({
      label: null,
      links: [
        { href: "/analisis-log-hp", label: "Análisis Logs HP", exact: false, icon: FileSearch },
      ],
    });
  }

  if (hasBonoTecnicos) {
    sections.push({
      label: null,
      links: [{ href: bonoTecnicosHref, label: "Bono Técnicos", exact: false, icon: Award }],
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
  hasAnalisisLogHp,
  hasBonoTecnicos,
  onNavigate,
}: {
  hasPrestadores: boolean;
  hasLiquidaciones: boolean;
  hasSla: boolean;
  hasPreventivos: boolean;
  hasAnalisisLogHp: boolean;
  hasBonoTecnicos: boolean;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const { can, hasFeature } = useSession();
  // Los flags `has*` dicen qué módulos tiene el usuario; el mapa central de
  // permisos por ruta (ADR-029) filtra además los ítems cuya pantalla pide
  // una acción específica.
  // Mismo criterio que vacaciones (ver sidebar.tsx::hrefDeModulo): si no
  // llega a la pantalla de "view" (la del supervisor con todos los
  // técnicos), el link va a la propia (cargar/ver sus solicitudes de TV).
  const bonoTecnicosHref = can("bono-tecnicos", "view") ? "/bono-tecnicos" : "/bono-tecnicos/solicitudes";
  const sections = buildSections({
    hasPrestadores,
    hasLiquidaciones,
    hasSla,
    hasPreventivos,
    hasAnalisisLogHp,
    hasBonoTecnicos,
    bonoTecnicosHref,
  })
    .map((s) => ({ ...s, links: s.links.filter((l) => canAccessPath(l.href, { can, hasFeature })) }))
    .filter((s) => s.links.length > 0);

  return (
    <div className="flex flex-col gap-3 py-1.5 pb-2 pl-4 pr-1">
      {sections.map((section) => (
        <div key={section.label ?? section.links[0]?.href} className="flex flex-col gap-px">
          {section.label && (
            <p className="px-2 pb-1 font-body text-[10px] font-bold uppercase tracking-[.08em] text-muted-foreground/70">
              {section.label}
            </p>
          )}
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
