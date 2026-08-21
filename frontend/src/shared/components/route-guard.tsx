"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { useSession } from "@/services/session-provider";
import { canAccessPath, moduleForRule, ruleForPath } from "@/shared/config/route-permissions";

/** Query param con el que `RouteGuard` manda a Inicio cuando la ruta pedida
 * excede los permisos; `AccessDeniedToast` lo consume y limpia la URL. */
const DENIED_PARAM = "sin-permiso";

/** Guard de ruta por permiso (ADR-029). Vive en el layout de `(app)` como
 * client component porque los layouts no se re-renderizan en navegaciones
 * suaves: solo algo que observe `usePathname()` ve cada cambio de ruta. No
 * renderiza la página mientras redirige, así no hay flash de una pantalla
 * que igual iba a devolver 403. El backend sigue siendo el enforcement real
 * (`require_permission`); esto es UX. */
export function RouteGuard({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { can, hasFeature } = useSession();
  const allowed = canAccessPath(pathname, { can, hasFeature });

  useEffect(() => {
    if (allowed) return;
    const rule = ruleForPath(pathname);
    const moduleKey = rule ? moduleForRule(rule) : "";
    router.replace(`/?${DENIED_PARAM}=${encodeURIComponent(moduleKey)}`);
  }, [allowed, pathname, router]);

  if (!allowed) return null;
  return <>{children}</>;
}

/** Muestra el toast de "sin permiso" al aterrizar en `/` desde el guard y
 * limpia el query param para que un refresh no lo repita. */
export function AccessDeniedToast() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const { modules } = useSession();
  const shown = useRef<string | null>(null);
  const denied = searchParams.get(DENIED_PARAM);

  useEffect(() => {
    if (denied === null || shown.current === denied) return;
    shown.current = denied;
    const label = modules.find((m) => m.key === denied)?.label ?? denied;
    toast.error(
      label
        ? `No tenés permiso para entrar a ${label}.`
        : "No tenés permiso para entrar a esa sección.",
      { description: "Pedile acceso a un administrador." },
    );
    router.replace(pathname);
  }, [denied, modules, pathname, router]);

  return null;
}
