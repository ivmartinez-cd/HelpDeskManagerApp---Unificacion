"use client";

import { useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart2,
  Bell,
  ChevronDown,
  Circle,
  Clock,
  FileSearch,
  Home,
  LogOut,
  Menu,
  Package,
  Settings,
  UserRound,
  Wrench,
  type LucideIcon,
  MessageCircle,
} from "lucide-react";
import { ThemeToggle } from "@/shared/components/theme-toggle";
import { ContadoresNavSubmenu } from "@/shared/components/contadores-nav-submenu";
import { InsumosNavSubmenu } from "@/shared/components/insumos-nav-submenu";
import { ServicioTecnicoNavSubmenu } from "@/shared/components/servicio-tecnico-nav-submenu";
import { VacacionesNavSubmenu } from "@/shared/components/vacaciones-nav-submenu";
import { cn } from "@/shared/utils/cn";
import { ChangePasswordModal } from "@/features/auth/components/change-password-modal";
import { useLogout } from "@/features/auth/hooks/use-logout";
import { useSession } from "@/services/session-provider";
import { UserAvatar } from "@/shared/components/ui/user-avatar";
import { WatiHeaderLink } from "@/features/wati/components/wati-header-link";

const MODULE_ICONS: Record<string, LucideIcon> = {
  contadores: BarChart2,
  insumos: Package,
  vacaciones: UserRound,
  turnos: Clock,
  "analisis-log-hp": FileSearch,
  wati: MessageCircle,
  admin: Settings,
};

export function Sidebar({
  children,
  watiUrl = null,
}: {
  children: ReactNode;
  /** URL del tenant de WATI, leída server-side en `app/(app)/layout.tsx`
   * (`WATI_URL`, no `NEXT_PUBLIC_*` -- ver docstring de `WatiHeaderLink`).
   * `null` = sin configurar, el ícono no se muestra. */
  watiUrl?: string | null;
}) {
  const { user, modules } = useSession();
  // Configuración es un módulo más para el backend (sort_order en la tabla
  // Module), pero en la nav siempre tiene que quedar al final del todo.
  const sortedModules = [...modules].sort((a, b) =>
    a.key === "admin" ? 1 : b.key === "admin" ? -1 : 0,
  );
  // Liquidaciones no se muestra como ítem propio de nivel superior: queda
  // anidado dentro de Prestadores (ver PrestadoresNavSubmenu). Sigue siendo
  // un módulo backend independiente, esto es solo reorganización visual.
  const liquidacionesModule = modules.find((m) => m.key === "liquidaciones");
  const prestadoresModule = modules.find((m) => m.key === "prestadores");
  const slaModule = modules.find((m) => m.key === "sla");
  const preventivosModule = modules.find((m) => m.key === "preventivos");
  const analisisLogHpModule = modules.find((m) => m.key === "analisis-log-hp");
  // prestadores, sla, liquidaciones, preventivos y analisis-log-hp se muestran
  // anidados bajo Servicio Técnico, no como ítems de nivel superior — solo
  // reorganización visual del sidebar.
  const topLevelModules = sortedModules.filter(
    (m) =>
      m.key !== "liquidaciones" &&
      m.key !== "prestadores" &&
      m.key !== "sla" &&
      m.key !== "preventivos" &&
      m.key !== "analisis-log-hp",
  );
  // El grupo "Servicio Técnico" no es un módulo del catálogo: se muestra solo si
  // el usuario tiene al menos uno de los módulos que agrupa (ADR-029; antes
  // aparecía siempre, apuntando a una ruta inexistente para quien no tenía nada).
  const servicioTecnicoVisible =
    !!prestadoresModule ||
    !!liquidacionesModule ||
    !!slaModule ||
    !!preventivosModule ||
    !!analisisLogHpModule;
  const { logout, loading } = useLogout();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  // Overrides manuales del chevron por módulo (`module.key`). Sin entrada =
  // sin override todavía: seguí el estado activo (auto-abierto al entrar a la
  // página). Una vez que el usuario clickea el chevron, pasa a mandar su
  // elección explícita en vez de la ruta actual — pero solo hasta la próxima
  // navegación real (ver resync de abajo): si no, colapsar el chevron y
  // después clickear el módulo para entrar dejaba el submenú escondido en la
  // propia página activa, aunque el chevron mostrara "colapsado" — un
  // desincronismo real detectado al verificar el fix.
  const [submenuOverride, setSubmenuOverride] = useState<Record<string, boolean>>({});
  const [prevPathname, setPrevPathname] = useState(pathname);
  if (pathname !== prevPathname) {
    setPrevPathname(pathname);
    setSubmenuOverride({});
  }

  const isActive = (route: string) => pathname === route || pathname.startsWith(`${route}/`);
  const closeMobile = () => setMobileOpen(false);
  const isHome = pathname === "/";

  return (
    <div className="flex h-screen w-full flex-col">
      <header className="flex h-16 flex-none items-center justify-between border-b border-border bg-card px-3 sm:px-4 lg:px-7">
        <div className="flex min-w-0 items-center gap-2 sm:gap-4">
          <button
            className="flex-none rounded-[8px] p-2 text-foreground hover:bg-muted lg:hidden"
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
            onClick={() => setChangePasswordOpen(true)}
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

      <div className="flex min-h-0 flex-1">
        <aside
          className={cn(
            "fixed inset-y-16 left-0 z-40 flex w-56 -translate-x-full transform flex-col overflow-y-auto thin-scrollbar border-r border-border bg-card p-3 transition-transform lg:static lg:inset-y-0 lg:translate-x-0",
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
                  : "text-muted-foreground hover:bg-muted",
              )}
            >
              <Home className="h-4 w-4 flex-none" aria-hidden="true" />
              Inicio
            </Link>

            {/* Servicio Técnico: grupo hardcodeado (no es módulo), expandible con
                los módulos que agrupa — mismo patrón que Prestadores +
                Liquidaciones pero en sentido inverso (el padre es el hardcodeado). */}
            {servicioTecnicoVisible && (() => {
              const stcActive =
                isActive("/servicio-tecnico") ||
                (!!slaModule && isActive("/sla")) ||
                (!!prestadoresModule && isActive("/prestadores")) ||
                (!!liquidacionesModule && isActive("/liquidaciones")) ||
                (!!preventivosModule && isActive("/preventivos")) ||
                (!!analisisLogHpModule && isActive("/analisis-log-hp"));
              const stcHasSubmenu =
                !!slaModule || !!prestadoresModule || !!preventivosModule || !!analisisLogHpModule;
              const stcSubmenuExpanded = submenuOverride["servicio-tecnico"] ?? stcActive;
              const stcHref = prestadoresModule
                ? "/prestadores"
                : slaModule
                  ? "/sla"
                  : "/servicio-tecnico";
              return (
                <div className="flex flex-col">
                  <div
                    className={cn(
                      "flex items-center rounded-[8px] transition-colors",
                      stcActive
                        ? "bg-brand-orange/[0.12] font-semibold text-brand-orange"
                        : "text-muted-foreground hover:bg-muted",
                    )}
                  >
                    <Link
                      href={stcHref}
                      onClick={closeMobile}
                      aria-current={stcActive ? "page" : undefined}
                      className="flex flex-1 items-center gap-2.5 px-3 py-2.5 font-body text-sm no-underline"
                    >
                      <Wrench className="h-4 w-4 flex-none" aria-hidden="true" />
                      Servicio Técnico
                    </Link>
                    {stcHasSubmenu && (
                      <button
                        type="button"
                        onClick={() =>
                          setSubmenuOverride((prev) => ({
                            ...prev,
                            "servicio-tecnico": !stcSubmenuExpanded,
                          }))
                        }
                        aria-expanded={stcSubmenuExpanded}
                        aria-label={
                          stcSubmenuExpanded
                            ? "Colapsar submenú de Servicio Técnico"
                            : "Expandir submenú de Servicio Técnico"
                        }
                        className="flex-none rounded-[6px] p-2 text-muted-foreground hover:text-foreground"
                      >
                        <ChevronDown
                          className={cn(
                            "h-3.5 w-3.5 transition-transform",
                            !stcSubmenuExpanded && "-rotate-90",
                          )}
                        />
                      </button>
                    )}
                  </div>
                  {stcHasSubmenu && stcSubmenuExpanded && (
                    <ServicioTecnicoNavSubmenu
                      hasPrestadores={!!prestadoresModule}
                      hasLiquidaciones={!!liquidacionesModule}
                      hasSla={!!slaModule}
                      hasPreventivos={!!preventivosModule}
                      hasAnalisisLogHp={!!analisisLogHpModule}
                      onNavigate={closeMobile}
                    />
                  )}
                </div>
              );
            })()}

            {modules.length === 0 && (
              <p className="px-3 py-4 font-body text-xs text-muted-foreground">
                Todavía no tenés módulos habilitados.
              </p>
            )}

            {topLevelModules.map((module) => {
              const isContadores = module.key === "contadores";
              const isInsumos = module.key === "insumos";
              const isVacaciones = module.key === "vacaciones";
              const active = isActive(module.route);
              const hasSubmenu = isContadores || isInsumos || isVacaciones;
              const submenuExpanded = submenuOverride[module.key] ?? active;
              const ModuleIcon = MODULE_ICONS[module.key] ?? Circle;
              return (
                <div key={module.key} className="flex flex-col">
                  <div
                    className={cn(
                      "flex items-center rounded-[8px] transition-colors",
                      active
                        ? "bg-brand-orange/[0.12] font-semibold text-brand-orange"
                        : "text-muted-foreground hover:bg-muted",
                    )}
                  >
                    <Link
                      href={isContadores ? "/contadores/calendario" : module.route}
                      onClick={closeMobile}
                      aria-current={active ? "page" : undefined}
                      className="flex flex-1 items-center gap-2.5 px-3 py-2.5 font-body text-sm no-underline"
                    >
                      <ModuleIcon className="h-4 w-4 flex-none" aria-hidden="true" />
                      {module.label}
                    </Link>
                    {hasSubmenu && (
                      <button
                        type="button"
                        onClick={() =>
                          setSubmenuOverride((prev) => ({
                            ...prev,
                            [module.key]: !submenuExpanded,
                          }))
                        }
                        aria-expanded={submenuExpanded}
                        aria-label={
                          submenuExpanded
                            ? `Colapsar submenú de ${module.label}`
                            : `Expandir submenú de ${module.label}`
                        }
                        className="flex-none rounded-[6px] p-2 text-muted-foreground hover:text-foreground"
                      >
                        <ChevronDown
                          className={cn(
                            "h-3.5 w-3.5 transition-transform",
                            !submenuExpanded && "-rotate-90",
                          )}
                        />
                      </button>
                    )}
                  </div>
                  {isContadores && submenuExpanded && (
                    <ContadoresNavSubmenu onNavigate={closeMobile} />
                  )}
                  {isInsumos && submenuExpanded && <InsumosNavSubmenu onNavigate={closeMobile} />}
                  {isVacaciones && submenuExpanded && (
                    <VacacionesNavSubmenu onNavigate={closeMobile} />
                  )}
                </div>
              );
            })}
          </nav>

          <div className="mt-auto border-t border-border px-3 pb-1 pt-3">
            <span className="font-body text-[11px] text-muted-foreground">
              Portal interno · Canal Directo
            </span>
          </div>
        </aside>

        {mobileOpen && (
          <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={closeMobile} />
        )}

        <main className="relative min-h-0 flex-1 overflow-y-auto thin-scrollbar bg-background">
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
