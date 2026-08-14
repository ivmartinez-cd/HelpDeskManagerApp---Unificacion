"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import {
  CalendarDays,
  Gauge,
  ReceiptText,
  UserRoundCheck,
  Workflow,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/shared/utils/cn";

/** Submenú de Contadores — mismo lenguaje visual que `InsumosNavSubmenu`
 * (ícono + acento naranja, pill activo) pero sin agrupar en secciones: son
 * pocos links y no forman categorías distintas como Insumos. */
interface NavLinkDef {
  href: string;
  label: string;
  icon: LucideIcon;
  active: boolean;
}

export function ContadoresNavSubmenu({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const tool = searchParams.get("tool");

  const links: NavLinkDef[] = [
    {
      href: "/contadores/calendario",
      label: "Calendario",
      icon: CalendarDays,
      active: pathname === "/contadores/calendario" || tool === "calendario",
    },
    {
      href: "/contadores/coberturas",
      label: "Coberturas",
      icon: UserRoundCheck,
      active: pathname === "/contadores/coberturas",
    },
    {
      href: "/contadores/equipos-sin-real",
      label: "Sin contador real",
      icon: Gauge,
      active: pathname === "/contadores/equipos-sin-real",
    },
    {
      href: "/contadores/anexos-pendientes",
      label: "Anexos sin facturar",
      icon: ReceiptText,
      active: pathname === "/contadores/anexos-pendientes",
    },
    {
      href: "/contadores",
      label: "Automatización",
      icon: Workflow,
      active: pathname === "/contadores" && tool !== "calendario",
    },
  ];

  return (
    <div className="flex flex-col gap-px py-1.5 pb-2 pl-6 pr-1">
      {links.map(({ href, label, icon: Icon, active }) => (
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
      ))}
    </div>
  );
}
