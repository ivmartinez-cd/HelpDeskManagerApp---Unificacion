"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Award,
  CalendarClock,
  ClipboardList,
  FileQuestion,
  FileSearch,
  Gauge,
  Headset,
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
  label: string;
  links: NavLinkDef[];
}

/** Submenú del grupo virtual "Servicio Técnico" (reorganizado 2026-08-28):
 *  cuatro secciones por tipo de trabajo, todas con título — Incidentes
 *  (tablero SLA + las tres colas de seguimiento), Prestadores, Técnicos y
 *  Herramientas. Liquidaciones ya no va acá: es un ítem de nivel superior
 *  propio (ver `LiquidacionesNavSubmenu`). Cada sección se arma solo con los
 *  links de los módulos que el usuario tiene; las vacías no se muestran. */
function buildSections({
  hasPrestadores,
  hasSla,
  hasPreventivos,
  hasAnalisisLogHp,
  hasBonoTecnicos,
  bonoTecnicosHref,
}: {
  hasPrestadores: boolean;
  hasSla: boolean;
  hasPreventivos: boolean;
  hasAnalisisLogHp: boolean;
  hasBonoTecnicos: boolean;
  bonoTecnicosHref: string;
}): NavSectionDef[] {
  const incidentes: NavLinkDef[] = hasSla
    ? [
        { href: "/sla", label: "Tablero SLA", exact: true, icon: Gauge },
        { href: "/sla/pendientes-a-cerrar", label: "Pendientes a cerrar", exact: false, icon: ClipboardList },
        { href: "/incidentes-sin-consultar", label: "Sin consultar", exact: false, icon: FileQuestion },
        { href: "/sla/mesa-de-ayuda", label: "Mesa de Ayuda", exact: false, icon: Headset },
      ]
    : [];

  const prestadores: NavLinkDef[] = hasPrestadores
    ? [
        { href: "/prestadores", label: "Asignados", exact: true, icon: Users },
        { href: "/prestadores/coberturas", label: "Coberturas", exact: false, icon: UserRoundCheck },
      ]
    : [];

  const tecnicos: NavLinkDef[] = [
    ...(hasPreventivos
      ? [{ href: "/preventivos", label: "Preventivos por zona", exact: false, icon: CalendarClock }]
      : []),
    ...(hasBonoTecnicos
      ? [{ href: bonoTecnicosHref, label: "Bono Técnicos", exact: false, icon: Award }]
      : []),
  ];

  const herramientas: NavLinkDef[] = hasAnalisisLogHp
    ? [{ href: "/analisis-log-hp", label: "Análisis Logs HP", exact: false, icon: FileSearch }]
    : [];

  return [
    { label: "Incidentes", links: incidentes },
    { label: "Prestadores", links: prestadores },
    { label: "Técnicos", links: tecnicos },
    { label: "Herramientas", links: herramientas },
  ];
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
  hasSla,
  hasPreventivos,
  hasAnalisisLogHp,
  hasBonoTecnicos,
  onNavigate,
}: {
  hasPrestadores: boolean;
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
