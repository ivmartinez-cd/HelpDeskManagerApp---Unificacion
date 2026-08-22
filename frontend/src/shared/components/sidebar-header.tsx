"use client";

import { Bell, LogOut, Menu } from "lucide-react";
import { ThemeToggle } from "@/shared/components/theme-toggle";
import type { UserSummary } from "@/features/auth/api/auth-api";
import { useLogout } from "@/features/auth/hooks/use-logout";
import { UserAvatar } from "@/shared/components/ui/user-avatar";
import { WatiHeaderLink } from "@/features/wati/components/wati-header-link";

export function SidebarHeader({
  user,
  watiUrl,
  onOpenMobile,
  onOpenChangePassword,
}: {
  user: UserSummary;
  watiUrl: string | null;
  onOpenMobile: () => void;
  onOpenChangePassword: () => void;
}) {
  const { logout, loading } = useLogout();
  return (
    <header className="flex h-16 flex-none items-center justify-between border-b border-border bg-card px-3 sm:px-4 lg:px-7">
      <div className="flex min-w-0 items-center gap-2 sm:gap-4">
        <button
          className="flex-none rounded-[8px] p-2 text-foreground hover:bg-muted lg:hidden"
          onClick={onOpenMobile}
          aria-label="Abrir menú"
        >
          <Menu className="h-5 w-5" />
        </button>
        {/* eslint-disable-next-line @next/next/no-img-element -- SVG, next/image no aporta acá */}
        <img
          src="/isotipo.svg"
          alt="Canal Directo"
          className="h-[30px] w-auto flex-none object-contain sm:hidden"
        />
        {/* eslint-disable-next-line @next/next/no-img-element -- SVG, next/image no aporta acá */}
        <img
          src="/logo.svg"
          alt="Canal Directo"
          className="hidden h-[34px] w-auto flex-none object-contain sm:block"
        />
        <div className="hidden h-[22px] w-px bg-border sm:block" />
        <span className="hidden font-heading text-[13px] font-bold tracking-[.06em] text-muted-foreground sm:block">
          MESA DE AYUDA
        </span>
      </div>

      <div className="flex flex-none items-center gap-1 sm:gap-3">
        <WatiHeaderLink url={watiUrl} />
        <Bell className="hidden h-5 w-5 text-muted-foreground sm:block" aria-hidden="true" />
        <div className="hidden h-[22px] w-px bg-border sm:block" />
        <button
          onClick={onOpenChangePassword}
          className="flex items-center gap-2.5 rounded-[8px] px-1.5 py-1 transition-colors hover:bg-muted"
          title="Cambiar contraseña"
        >
          <UserAvatar fullName={user.fullName} color={user.color} />
          <span className="hidden flex-col items-start leading-[1.25] sm:flex">
            <span className="font-body text-[13px] font-semibold text-foreground">
              {user.fullName}
            </span>
            <span className="font-body text-xs text-muted-foreground">
              {user.isSuperadmin ? "Administrador" : "Usuario"}
            </span>
          </span>
        </button>
        <ThemeToggle />
        <button
          onClick={() => logout()}
          disabled={loading}
          className="rounded-[8px] p-2 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-50"
          title="Cerrar sesión"
          aria-label="Cerrar sesión"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
