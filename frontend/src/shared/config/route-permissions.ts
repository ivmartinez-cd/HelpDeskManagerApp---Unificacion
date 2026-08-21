/** Mapa central ruta → permiso requerido (ADR-029).
 *
 * Única fuente de verdad del frontend para "¿esta persona puede abrir esta
 * URL?". Lo consumen:
 *  - `RouteGuard` (layout de `(app)`): redirige a `/` con toast si no alcanza.
 *  - los submenús del sidebar: ocultan los ítems a los que no se puede entrar.
 *
 * El enforcement real sigue siendo el backend (`require_permission`): esto es
 * UX, para que nadie aterrice en una pantalla que solo devuelve 403. Por eso
 * una ruta sin entrada acá **no se bloquea** (fail-open a nivel página): una
 * pantalla nueva sin mapear sigue siendo usable y el backend la protege igual.
 *
 * Orden: se toma la primera entrada cuyo `prefix` matchea (`===` o `/…`; con
 * `exact: true` solo `===`), así que lo específico va antes que lo general
 * (`/vacaciones/aprobaciones` antes que `/vacaciones`). `anyOf` = alcanza con
 * uno de los permisos listados.
 *
 * Regla al agregar un módulo o pantalla: seed en el catálogo (migración) +
 * `well_known_permissions.py` + entrada acá + `can()` en los botones de
 * mutación. Ver ARCHITECTURE_GUIDE.md §8 "Autorización por módulo". */

export interface RequiredPermission {
  module: string;
  action: string;
}

interface RouteRule {
  prefix: string;
  anyOf: RequiredPermission[];
  /** Solo la ruta exacta, no sus sub-rutas (para un hub cuya raíz pide más
   * permiso que sus hijas). */
  exact?: boolean;
}

const p = (module: string, action: string): RequiredPermission => ({ module, action });

export const ROUTE_RULES: readonly RouteRule[] = [
  // Configuración (usuarios + permisos). Turnos ya no vive acá (ADR-029).
  { prefix: "/admin", anyOf: [p("admin", "manage")] },

  // Turnos: la grilla y sus coberturas se consultan con view; mutar es manage
  // (gateado por botón, no por ruta).
  { prefix: "/turnos", anyOf: [p("turnos", "view")] },

  // Gestión de Personal: espejo del submenú (vacaciones-nav-submenu.tsx). Un
  // operador (view + create) ve por ahora SOLO Solicitudes (decisión del
  // usuario 2026-08-21); dashboard, asistencias y gestión humana son del TL/admin.
  { prefix: "/vacaciones/solicitudes", anyOf: [p("vacaciones", "manage"), p("vacaciones", "create")] },
  { prefix: "/vacaciones/aprobaciones", anyOf: [p("vacaciones", "manage"), p("vacaciones", "approve")] },
  { prefix: "/vacaciones/asistencias", anyOf: [p("vacaciones", "manage"), p("vacaciones", "approve")] },
  { prefix: "/vacaciones/gestion", anyOf: [p("vacaciones", "manage")] },
  { prefix: "/vacaciones/reportes", anyOf: [p("vacaciones", "manage")] },
  { prefix: "/vacaciones/auditoria", anyOf: [p("vacaciones", "manage")] },
  { prefix: "/vacaciones/configuracion", anyOf: [p("vacaciones", "manage")] },
  // Dashboard del equipo (raíz del módulo): TL/admin.
  { prefix: "/vacaciones", exact: true, anyOf: [p("vacaciones", "manage"), p("vacaciones", "approve")] },
  { prefix: "/vacaciones", anyOf: [p("vacaciones", "view")] },

  // Contadores: el hub raíz ("Automatización": DB3, proyección, FTP, SDS, ERS…)
  // son todas herramientas cuyos endpoints exigen `contadores.export`
  // (tools/ftp_clients/sds/ers routers); calendario, coberturas, equipos sin
  // real y anexos se abren con `view`.
  { prefix: "/contadores", exact: true, anyOf: [p("contadores", "export")] },
  // Coberturas y anexos sin facturar son gestión del equipo/facturación: solo
  // con `manage` (decisión del usuario 2026-08-21: los operadores no los ven).
  { prefix: "/contadores/coberturas", anyOf: [p("contadores", "manage")] },
  { prefix: "/contadores/anexos-pendientes", anyOf: [p("contadores", "manage")] },
  // Resto: la página entera se abre con view; las acciones se gatean adentro.
  { prefix: "/contadores", anyOf: [p("contadores", "view")] },
  { prefix: "/insumos", anyOf: [p("insumos", "view")] },
  { prefix: "/liquidaciones", anyOf: [p("liquidaciones", "view")] },
  // Coberturas de prestadores: solo para quien las opera (crear/editar); con
  // `view` a secas se ve el directorio de PST pero no esta pantalla
  // (decisión del usuario, 2026-08-21: los operadores no la ven).
  {
    prefix: "/prestadores/coberturas",
    anyOf: [p("prestadores", "create"), p("prestadores", "update")],
  },
  { prefix: "/prestadores", anyOf: [p("prestadores", "view")] },
  { prefix: "/sla", anyOf: [p("sla", "view")] },
  { prefix: "/preventivos", anyOf: [p("preventivos", "view")] },
  { prefix: "/analisis-log-hp", anyOf: [p("analisis-log-hp", "view")] },
  { prefix: "/wati", anyOf: [p("wati", "view")] },
];

function matches(rule: RouteRule, pathname: string): boolean {
  if (pathname === rule.prefix) return true;
  return !rule.exact && pathname.startsWith(`${rule.prefix}/`);
}

/** Primera regla que aplica al pathname (sin query string), o `null` si la
 * ruta no está mapeada (solo login). */
export function ruleForPath(pathname: string): RouteRule | null {
  const clean = pathname.split("?")[0] ?? pathname;
  return ROUTE_RULES.find((r) => matches(r, clean)) ?? null;
}

/** `can` es el de `useSession()` (ya contempla superadmin). */
export function canAccessPath(
  pathname: string,
  can: (module: string, action: string) => boolean,
): boolean {
  const rule = ruleForPath(pathname);
  if (!rule) return true;
  return rule.anyOf.some((perm) => can(perm.module, perm.action));
}
