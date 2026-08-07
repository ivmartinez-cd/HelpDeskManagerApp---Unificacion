"use client";

import { useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { KeyRound, LogOut, Menu } from "lucide-react";
import { ThemeToggle } from "@/shared/components/theme-toggle";
import { HelpDeskLogo } from "@/shared/components/helpdesk-logo";
import { resolveIcon } from "@/shared/components/icon-registry";
import { cn } from "@/shared/utils/cn";
import { ChangePasswordModal } from "@/features/auth/components/change-password-modal";
import { useLogout } from "@/features/auth/hooks/use-logout";
import { useSession } from "@/services/session-provider";

export function Sidebar({ children }: { children: ReactNode }) {
  const { user, modules } = useSession();
  const { logout, loading } = useLogout();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);

  const isActive = (route: string) => pathname === route || pathname.startsWith(`${route}/`);

  return (
    <div className="flex h-full w-full">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 -translate-x-full transform flex-col bg-[#18181b] border-r border-white/5 transition-transform lg:translate-x-0",
          mobileOpen && "translate-x-0",
        )}
      >
        <div className="flex h-16 items-center border-b border-white/10 px-5">
          <HelpDeskLogo />
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto thin-scrollbar p-3">
          {modules.length === 0 && (
            <p className="px-3 py-4 text-xs text-white/40">
              Todavía no tenés módulos habilitados.
            </p>
          )}
          {modules.map((module) => {
            const Icon = resolveIcon(module.icon);
            return (
              <Link
                key={module.key}
                href={module.route}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive(module.route)
                    ? "bg-accent text-accent-foreground shadow-md shadow-accent/30"
                    : "text-white/60 hover:bg-white/8 hover:text-white",
                )}
              >
                <Icon className="h-4.5 w-4.5 shrink-0" />
                {module.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <div className="flex flex-1 flex-col overflow-hidden lg:pl-64">
        <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center justify-between border-b border-border bg-card/90 px-4 backdrop-blur lg:px-6">
          <button
            className="rounded-lg p-2 hover:bg-muted lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Abrir menú"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setChangePasswordOpen(true)}
              className="hidden rounded-xl px-2 py-1 text-right transition-colors hover:bg-muted sm:block"
              title="Cambiar contraseña"
            >
              <p className="text-xs font-black leading-none text-foreground uppercase tracking-tight">
                {user.fullName}
              </p>
              <p className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest mt-0.5">
                {user.isSuperadmin ? "Superadmin" : "Usuario"}
              </p>
            </button>
            <button
              onClick={() => setChangePasswordOpen(true)}
              className="rounded-xl p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-all duration-150 sm:hidden"
              title="Cambiar contraseña"
              aria-label="Cambiar contraseña"
            >
              <KeyRound className="h-4 w-4" />
            </button>
            <ThemeToggle />
            <button
              onClick={() => logout()}
              disabled={loading}
              className="rounded-xl p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-all duration-150 disabled:opacity-50"
              title="Cerrar sesión"
              aria-label="Cerrar sesión"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>

        <div className="relative flex-1 overflow-y-auto thin-scrollbar">{children}</div>
      </div>

      <ChangePasswordModal
        isOpen={changePasswordOpen}
        onClose={() => setChangePasswordOpen(false)}
      />
    </div>
  );
}
