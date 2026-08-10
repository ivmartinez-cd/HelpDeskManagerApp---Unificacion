"use client";

import { useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, ChevronDown, LogOut, Menu } from "lucide-react";
import { ThemeToggle } from "@/shared/components/theme-toggle";
import { ContadoresNavSubmenu } from "@/shared/components/contadores-nav-submenu";
import { cn } from "@/shared/utils/cn";
import { ChangePasswordModal } from "@/features/auth/components/change-password-modal";
import { useLogout } from "@/features/auth/hooks/use-logout";
import { useSession } from "@/services/session-provider";

function getInitials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase();
}

export function Sidebar({ children }: { children: ReactNode }) {
  const { user, modules } = useSession();
  const { logout, loading } = useLogout();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  // `null` = sin override manual todavía, seguí el estado activo (auto-abierto
  // al entrar a la página). Una vez que el usuario clickea el chevron, pasa a
  // mandar su elección explícita en vez de la ruta actual — pero solo hasta
  // la próxima navegación real (ver resync de abajo): si no, colapsar el
  // chevron y después clickear "Contadores" para entrar dejaba el submenú
  // escondido en la propia página activa, aunque el chevron mostrara
  // "colapsado" — un desincronismo real detectado al verificar el fix.
  const [contadoresExpandedOverride, setContadoresExpandedOverride] = useState<boolean | null>(
    null,
  );
  const [prevPathname, setPrevPathname] = useState(pathname);
  if (pathname !== prevPathname) {
    setPrevPathname(pathname);
    setContadoresExpandedOverride(null);
  }

  const isActive = (route: string) => pathname === route || pathname.startsWith(`${route}/`);
  const closeMobile = () => setMobileOpen(false);
  const isHome = pathname === "/";

  return (
    <div className="flex h-screen w-full flex-col">
      <header className="flex h-16 flex-none items-center justify-between border-b border-black/[0.08] bg-white px-3 sm:px-4 lg:px-7">
        <div className="flex min-w-0 items-center gap-2 sm:gap-4">
          <button
            className="flex-none rounded-[8px] p-2 text-brand-charcoal hover:bg-black/5 lg:hidden"
            onClick={() => setMobileOpen(true)}
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
          <div className="hidden h-[22px] w-px bg-black/10 sm:block" />
          <span className="hidden font-heading text-[13px] font-bold tracking-[.06em] text-brand-gray sm:block">
            MESA DE AYUDA
          </span>
        </div>

        <div className="mx-8 hidden max-w-[440px] flex-1 md:block">
          <input
            disabled
            placeholder="Buscador próximamente..."
            aria-label="Buscar (próximamente)"
            className="w-full rounded-[8px] border border-black/[0.12] bg-brand-surface px-[14px] py-[9px] font-body text-sm text-brand-charcoal outline-none placeholder:text-[#a8a8a8] disabled:cursor-not-allowed disabled:opacity-70"
          />
        </div>

        <div className="flex flex-none items-center gap-1 sm:gap-3">
          <Bell className="hidden h-5 w-5 text-[#8a8a8c] sm:block" aria-hidden="true" />
          <div className="hidden h-[22px] w-px bg-black/10 sm:block" />
          <button
            onClick={() => setChangePasswordOpen(true)}
            className="flex items-center gap-2.5 rounded-[8px] px-1.5 py-1 transition-colors hover:bg-black/5"
            title="Cambiar contraseña"
          >
            <span className="flex h-[34px] w-[34px] flex-none items-center justify-center rounded-full bg-brand-gray font-heading text-[13px] font-bold text-white">
              {getInitials(user.fullName)}
            </span>
            <span className="hidden flex-col items-start leading-[1.25] sm:flex">
              <span className="font-body text-[13px] font-semibold text-brand-charcoal">
                {user.fullName}
              </span>
              <span className="font-body text-xs text-[#9a9a9a]">
                {user.isSuperadmin ? "Superadmin" : "Usuario"}
              </span>
            </span>
          </button>
          <ThemeToggle />
          <button
            onClick={() => logout()}
            disabled={loading}
            className="rounded-[8px] p-2 text-[#8a8a8c] hover:bg-black/5 hover:text-brand-charcoal disabled:opacity-50"
            title="Cerrar sesión"
            aria-label="Cerrar sesión"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <aside
          className={cn(
            "fixed inset-y-16 left-0 z-40 flex w-56 -translate-x-full transform flex-col overflow-y-auto thin-scrollbar border-r border-black/[0.08] bg-white p-3 transition-transform lg:static lg:inset-y-0 lg:translate-x-0",
            mobileOpen && "translate-x-0",
          )}
        >
          <nav className="flex flex-col gap-0.5">
            <Link
              href="/"
              onClick={closeMobile}
              aria-current={isHome ? "page" : undefined}
              className={cn(
                "flex items-center gap-2.5 rounded-[8px] px-3 py-2.5 font-body text-sm no-underline transition-colors",
                isHome
                  ? "bg-brand-orange/[0.12] font-semibold text-brand-orange"
                  : "text-[#4b4b4b] hover:bg-black/[0.03]",
              )}
            >
              <span
                className={cn(
                  "h-[7px] w-[7px] flex-none rounded-full",
                  isHome ? "bg-brand-orange" : "bg-[#d8d8d8]",
                )}
              />
              Inicio
            </Link>

            {modules.length === 0 && (
              <p className="px-3 py-4 font-body text-xs text-[#9a9a9a]">
                Todavía no tenés módulos habilitados.
              </p>
            )}

            {modules.map((module) => {
              const active = isActive(module.route);
              const isContadores = module.key === "contadores";
              const contadoresExpanded = contadoresExpandedOverride ?? active;
              return (
                <div key={module.key} className="flex flex-col">
                  <div
                    className={cn(
                      "flex items-center rounded-[8px] transition-colors",
                      active
                        ? "bg-brand-orange/[0.12] font-semibold text-brand-orange"
                        : "text-[#4b4b4b] hover:bg-black/[0.03]",
                    )}
                  >
                    <Link
                      href={module.route}
                      onClick={closeMobile}
                      aria-current={active ? "page" : undefined}
                      className="flex flex-1 items-center gap-2.5 px-3 py-2.5 font-body text-sm no-underline"
                    >
                      <span
                        className={cn(
                          "h-[7px] w-[7px] flex-none rounded-full",
                          active ? "bg-brand-orange" : "bg-[#d8d8d8]",
                        )}
                      />
                      {module.label}
                    </Link>
                    {isContadores && (
                      <button
                        type="button"
                        onClick={() => setContadoresExpandedOverride(!contadoresExpanded)}
                        aria-expanded={contadoresExpanded}
                        aria-label={
                          contadoresExpanded
                            ? "Colapsar submenú de Contadores"
                            : "Expandir submenú de Contadores"
                        }
                        className="flex-none rounded-[6px] p-2 text-[#b5b5b5] hover:text-brand-charcoal"
                      >
                        <ChevronDown
                          className={cn(
                            "h-3.5 w-3.5 transition-transform",
                            !contadoresExpanded && "-rotate-90",
                          )}
                        />
                      </button>
                    )}
                  </div>
                  {isContadores && contadoresExpanded && (
                    <ContadoresNavSubmenu onNavigate={closeMobile} />
                  )}
                </div>
              );
            })}
          </nav>

          <div className="mt-auto border-t border-black/[0.06] px-3 pb-1 pt-3">
            <span className="font-body text-[11px] text-brand-muted">
              Portal interno · Canal Directo
            </span>
          </div>
        </aside>

        {mobileOpen && (
          <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={closeMobile} />
        )}

        <main className="relative min-h-0 flex-1 overflow-y-auto thin-scrollbar bg-brand-surface">
          {children}
        </main>
      </div>

      <ChangePasswordModal
        isOpen={changePasswordOpen}
        onClose={() => setChangePasswordOpen(false)}
      />
    </div>
  );
}
