"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { cn } from "@/shared/utils/cn";

export function ContadoresNavSubmenu({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const tool = searchParams.get("tool");

  const isCalendarioActive =
    pathname === "/contadores/calendario" || tool === "calendario";
  const isAutomatizacionActive =
    pathname === "/contadores" && tool !== "calendario";

  return (
    <div className="flex flex-col gap-px py-1 pb-1.5 pl-6">
      <Link
        href="/contadores/calendario"
        onClick={onNavigate}
        className={cn(
          "rounded-[6px] px-2 py-1.5 font-body text-[13px] no-underline transition-colors",
          isCalendarioActive
            ? "bg-brand-orange/[0.08] font-bold text-brand-orange"
            : "text-[#7a7a7a] hover:text-brand-charcoal hover:bg-black/[0.04]",
        )}
      >
        Calendario
      </Link>
      <Link
        href="/contadores"
        onClick={onNavigate}
        className={cn(
          "rounded-[6px] px-2 py-1.5 font-body text-[13px] no-underline transition-colors",
          isAutomatizacionActive
            ? "bg-brand-orange/[0.08] font-bold text-brand-orange"
            : "text-[#7a7a7a] hover:text-brand-charcoal hover:bg-black/[0.04]",
        )}
      >
        Automatización
      </Link>
    </div>
  );
}
