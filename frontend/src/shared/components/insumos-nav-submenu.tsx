"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  ClipboardList,
  History,
  Monitor,
  MonitorOff,
  Settings,
  Users,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { useInsumosNavCounts } from "@/features/insumos/hooks/use-insumos-nav-counts";

/** Submenú de Insumos en la barra lateral, con el patrón de secciones +
 * badges del mockup del handoff (antes era una lista plana de 7 links sin
 * agrupar, sin iconos, sin contadores — ver `git log` de este archivo).
 * "Historial de pedidos" queda deliberadamente sin el acento naranja de los
 * demás items: es la única pantalla de solo-consulta del grupo, el resto son
 * vistas operativas. */
interface NavLinkDef {
  href: string;
  label: string;
  exact: boolean;
  icon: LucideIcon;
  accent?: boolean;
  badge?: "solicitudes" | "offline";
}

interface NavSectionDef {
  label: string;
  links: NavLinkDef[];
}

const SECTIONS: NavSectionDef[] = [
  {
    label: "Principal",
    links: [
      {
        href: "/insumos",
        label: "Solicitudes",
        exact: true,
        icon: ClipboardList,
        accent: true,
        badge: "solicitudes",
      },
      { href: "/insumos/historial", label: "Historial de pedidos", exact: false, icon: History },
    ],
  },
  {
    label: "Equipos",
    links: [
      {
        href: "/insumos/equipos-nuevos",
        label: "Sin registrar",
        exact: false,
        icon: Monitor,
        accent: true,
      },
      {
        href: "/insumos/equipos-offline",
        label: "Equipos offline",
        exact: false,
        icon: MonitorOff,
        accent: true,
        badge: "offline",
      },
    ],
  },
  {
    label: "Administración",
    links: [
      { href: "/insumos/clientes", label: "Clientes", exact: false, icon: Users, accent: true },
      {
        href: "/insumos/configuracion",
        label: "Configuración",
        exact: false,
        icon: Settings,
        accent: true,
      },
      {
        href: "/insumos/estadisticas",
        label: "Estadísticas",
        exact: false,
        icon: BarChart3,
        accent: true,
      },
    ],
  },
];

function CountPill({ value, tone }: { value: number; tone: "orange" | "red" }) {
  if (value <= 0) return null;
  return (
    <span
      className={cn(
        "inline-flex h-[18px] min-w-[18px] flex-none items-center justify-center rounded-full px-1 font-body text-[10px] font-bold tabular-nums text-white",
        tone === "red" ? "bg-[#ef4444]" : "bg-brand-orange",
      )}
    >
      {value}
    </span>
  );
}

function NavLinkRow({
  link,
  active,
  counts,
  onNavigate,
}: {
  link: NavLinkDef;
  active: boolean;
  counts: ReturnType<typeof useInsumosNavCounts>;
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
          : link.accent
            ? "text-brand-orange/85 hover:bg-muted hover:text-brand-orange"
            : "text-muted-foreground hover:bg-muted hover:text-foreground",
      )}
    >
      <Icon className="h-3.5 w-3.5 flex-none" aria-hidden="true" />
      <span className="flex-1 truncate">{link.label}</span>
      {link.badge === "solicitudes" && (
        <span className="flex flex-none items-center gap-1">
          <CountPill value={counts.pending} tone="orange" />
          <CountPill value={counts.critical} tone="red" />
        </span>
      )}
      {link.badge === "offline" && <CountPill value={counts.offline} tone="red" />}
    </Link>
  );
}

export function InsumosNavSubmenu({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const counts = useInsumosNavCounts();

  return (
    <div className="flex flex-col gap-3 py-1.5 pb-2 pl-6 pr-1">
      {SECTIONS.map((section) => (
        <div key={section.label} className="flex flex-col gap-px">
          <p className="px-2 pb-1 font-body text-[10px] font-bold uppercase tracking-[.08em] text-muted-foreground/70">
            {section.label}
          </p>
          {section.links.map((link) => {
            const active = link.exact
              ? pathname === link.href
              : pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <NavLinkRow
                key={link.href}
                link={link}
                active={active}
                counts={counts}
                onNavigate={onNavigate}
              />
            );
          })}
        </div>
      ))}
    </div>
  );
}
