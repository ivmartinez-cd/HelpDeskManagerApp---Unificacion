"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  DollarSign,
  FileText,
  LayoutDashboard,
  Map,
  ScrollText,
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
  label: string | null;
  links: NavLinkDef[];
}

/** Submenú de Liquidaciones como ítem de nivel superior (desde 2026-08-28;
 * antes vivía anidado dentro del grupo "Servicio Técnico", donde sus 7 links
 * eran casi la mitad del submenú y su "Configuración" se confundía con el
 * módulo Configuración de la app). El catálogo "Prestadores" de acá es el de
 * facturación, no el de Servicio Técnico > Prestadores (asignación
 * operador/Siges/SLA). */
const SECTIONS: NavSectionDef[] = [
  {
    label: null,
    links: [
      { href: "/liquidaciones", label: "Resumen", exact: true, icon: LayoutDashboard },
      { href: "/liquidaciones/lista", label: "Listado", exact: false, icon: FileText },
    ],
  },
  {
    label: "Configuración",
    links: [
      { href: "/liquidaciones/configuracion/prestadores", label: "Prestadores", exact: false, icon: Users },
      { href: "/liquidaciones/configuracion/spsts", label: "SPSTs", exact: false, icon: ScrollText },
      { href: "/liquidaciones/configuracion/tarifarios", label: "Tarifarios", exact: false, icon: DollarSign },
      { href: "/liquidaciones/configuracion/tabla-km", label: "Tabla KM", exact: false, icon: Map },
      { href: "/liquidaciones/configuracion/reglas", label: "Reglas de alerta", exact: false, icon: ScrollText },
    ],
  },
];

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

export function LiquidacionesNavSubmenu({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <div className="flex flex-col gap-3 py-1.5 pb-2 pl-4 pr-1">
      {SECTIONS.map((section) => (
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
