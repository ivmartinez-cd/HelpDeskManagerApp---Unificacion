"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/shared/utils/cn";

/** Submenú de Insumos en la barra lateral — misma forma que
 * `contadores-nav-submenu.tsx`, pero acá cada entrada es una ruta de archivo
 * propia (no hay `?tool=`): el módulo no tiene hub, `/insumos` ES el Dashboard. */
const LINKS = [
  { href: "/insumos", label: "Dashboard", exact: true },
  { href: "/insumos/clientes", label: "Clientes", exact: false },
  { href: "/insumos/equipos-nuevos", label: "Equipos Nuevos", exact: false },
  { href: "/insumos/historial", label: "Historial", exact: false },
  // Prefijo, no exacto: el detalle de cliente
  // (/insumos/estadisticas/clientes/:id) tiene que dejar Estadísticas activo.
  { href: "/insumos/estadisticas", label: "Estadísticas", exact: false },
  { href: "/insumos/configuracion", label: "Configuración", exact: false },
];

export function InsumosNavSubmenu({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <div className="flex flex-col gap-px py-1 pb-1.5 pl-6">
      {LINKS.map(({ href, label, exact }) => {
        const active = exact
          ? pathname === href
          : pathname === href || pathname.startsWith(`${href}/`);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={cn(
              "rounded-[6px] px-2 py-1.5 font-body text-[13px] no-underline transition-colors",
              active
                ? "bg-brand-orange/[0.08] font-bold text-brand-orange"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            {label}
          </Link>
        );
      })}
    </div>
  );
}
