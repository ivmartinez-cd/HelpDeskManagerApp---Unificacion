"use client";

import { useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home } from "lucide-react";
import { ModuleNavItem } from "@/shared/components/module-nav-item";
import { ServicioTecnicoNavItem } from "@/shared/components/servicio-tecnico-nav-item";
import { SidebarHeader } from "@/shared/components/sidebar-header";
import { cn } from "@/shared/utils/cn";
import { ChangePasswordModal } from "@/features/auth/components/change-password-modal";
import { useSession } from "@/services/session-provider";
import { canAccessPath } from "@/shared/config/route-permissions";

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
  const { user, modules, can, hasFeature } = useSession();
  // Destino del ítem de nivel superior de cada módulo: la raíz del módulo, salvo
  // que la ruta raíz pida más permiso del que tiene el usuario (mapa central de
  // rutas, ADR-029) — entonces la primera sub-pantalla accesible. Ej.: operador
  // de Gestión de Personal sin acceso al dashboard → Solicitudes.
  const hrefDeModulo = (module: { key: string; route: string }): string => {
    if (module.key === "contadores") return "/contadores/calendario";
    if (module.key === "vacaciones" && !canAccessPath(module.route, { can, hasFeature })) {
      return "/vacaciones/solicitudes";
    }
    return module.route;
  };
  // Orden del sidebar (pedido explícito del usuario 2026-08-25): los módulos
  // de uso diario van primero y en orden alfabético (Contadores, Insumos,
  // Servicio Técnico -grupo virtual-, WhatsApp); el resto (Gestión de
  // Personal, Turnos) queda debajo, sin orden alfabético entre sí; y
  // Configuración siempre al final de todo, sin importar sort_order del
  // backend.
  const DAILY_RANK: Record<string, number> = {
    contadores: 0,
    insumos: 1,
    "servicio-tecnico": 2,
    wati: 3,
  };
  const rankOf = (key: string) => {
    if (key === "admin") return 1000;
    return DAILY_RANK[key] ?? 100;
  };
  const sortedModules = [...modules].sort((a, b) => rankOf(a.key) - rankOf(b.key));
  // Liquidaciones no se muestra como ítem propio de nivel superior: queda
  // anidado dentro de Prestadores (ver PrestadoresNavSubmenu). Sigue siendo
  // un módulo backend independiente, esto es solo reorganización visual.
  const liquidacionesModule = modules.find((m) => m.key === "liquidaciones");
  const prestadoresModule = modules.find((m) => m.key === "prestadores");
  const slaModule = modules.find((m) => m.key === "sla");
  const preventivosModule = modules.find((m) => m.key === "preventivos");
  const analisisLogHpModule = modules.find((m) => m.key === "analisis-log-hp");
  const bonoTecnicosModule = modules.find((m) => m.key === "bono-tecnicos");
  // prestadores, sla, liquidaciones, preventivos, analisis-log-hp y
  // bono-tecnicos se muestran anidados bajo Servicio Técnico, no como ítems
  // de nivel superior — solo reorganización visual del sidebar.
  const topLevelModules = sortedModules.filter(
    (m) =>
      m.key !== "liquidaciones" &&
      m.key !== "prestadores" &&
      m.key !== "sla" &&
      m.key !== "preventivos" &&
      m.key !== "analisis-log-hp" &&
      m.key !== "bono-tecnicos",
  );
  // El grupo "Servicio Técnico" no es un módulo del catálogo: se muestra solo si
  // el usuario tiene al menos uno de los módulos que agrupa (ADR-029; antes
  // aparecía siempre, apuntando a una ruta inexistente para quien no tenía nada).
  const servicioTecnicoVisible =
    !!prestadoresModule ||
    !!liquidacionesModule ||
    !!slaModule ||
    !!preventivosModule ||
    !!analisisLogHpModule ||
    !!bonoTecnicosModule;
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
  const toggleSubmenu = (key: string) => (expanded: boolean) =>
    setSubmenuOverride((prev) => ({ ...prev, [key]: expanded }));

  return (
    <div className="flex h-screen w-full flex-col">
      <SidebarHeader
        user={user}
        watiUrl={watiUrl}
        onOpenMobile={() => setMobileOpen(true)}
        onOpenChangePassword={() => setChangePasswordOpen(true)}
      />

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

            {modules.length === 0 && (
              <p className="px-3 py-4 font-body text-xs text-muted-foreground">
                Todavía no tenés módulos habilitados.
              </p>
            )}

            {topLevelModules
              .filter((module) => rankOf(module.key) < DAILY_RANK["servicio-tecnico"])
              .map((module) => (
                <ModuleNavItem
                  key={module.key}
                  module={module}
                  href={hrefDeModulo(module)}
                  active={isActive(module.route)}
                  submenuOverride={submenuOverride[module.key]}
                  onToggleSubmenu={toggleSubmenu(module.key)}
                  onNavigate={closeMobile}
                />
              ))}

            {servicioTecnicoVisible && (
              <ServicioTecnicoNavItem
                hasSla={!!slaModule}
                hasPrestadores={!!prestadoresModule}
                hasLiquidaciones={!!liquidacionesModule}
                hasPreventivos={!!preventivosModule}
                hasAnalisisLogHp={!!analisisLogHpModule}
                hasBonoTecnicos={!!bonoTecnicosModule}
                isActive={isActive}
                submenuOverride={submenuOverride["servicio-tecnico"]}
                onToggleSubmenu={toggleSubmenu("servicio-tecnico")}
                onNavigate={closeMobile}
              />
            )}

            {topLevelModules
              .filter((module) => rankOf(module.key) >= DAILY_RANK["servicio-tecnico"])
              .map((module) => (
                <ModuleNavItem
                  key={module.key}
                  module={module}
                  href={hrefDeModulo(module)}
                  active={isActive(module.route)}
                  submenuOverride={submenuOverride[module.key]}
                  onToggleSubmenu={toggleSubmenu(module.key)}
                  onNavigate={closeMobile}
                />
              ))}
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
