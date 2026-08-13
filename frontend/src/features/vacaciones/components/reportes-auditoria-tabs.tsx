"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/shared/utils/cn";

const TABS = [
  { href: "/vacaciones/reportes", label: "Reportes" },
  { href: "/vacaciones/auditoria", label: "Auditoría" },
];

/** Tab bar pill del handoff 04: Reportes y Auditoría comparten el mismo
 * lenguaje visual pero viven en rutas propias (cada una con su ítem de nav). */
export function ReportesAuditoriaTabs() {
  const pathname = usePathname();
  return (
    <nav aria-label="Reportes y auditoría" className="flex gap-2">
      {TABS.map(({ href, label }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "rounded-[20px] px-5 py-2 font-body text-[13.5px] font-semibold no-underline transition-colors",
              active
                ? "bg-brand-orange text-white"
                : "bg-muted text-muted-foreground hover:text-foreground",
            )}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
