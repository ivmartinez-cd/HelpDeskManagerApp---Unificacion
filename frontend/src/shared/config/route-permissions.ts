/** Mapa central ruta → requisito de acceso (ADR-029, ADR-032).
 *
 * Única fuente de verdad del frontend para "¿esta persona puede abrir esta
 * URL?". Lo consumen:
 *  - `RouteGuard` (layout de `(app)`): redirige a `/` con toast si no alcanza.
 *  - los submenús del sidebar: ocultan los ítems a los que no se puede entrar.
 *
 * El enforcement real sigue siendo el backend (`require_permission` /
 * `require_feature`): esto es UX, para que nadie aterrice en una pantalla que
 * solo devuelve 403. Por eso una ruta sin entrada acá **no se bloquea**
 * (fail-open a nivel página): una pantalla nueva sin mapear sigue siendo
 * usable y el backend la protege igual.
 *
 * Dos tipos de requisito:
 *  - `anyOf`: alcanza con una de las acciones (módulo × acción) listadas.
 *  - `feature`: la pantalla es una "función" concedible por usuario desde la
 *    grilla de permisos (ADR-032). Es lo que permite "a este operador sí
 *    Coberturas, a aquel no" sin tocar código.
 *  Si una regla trae los dos, alcanza con cualquiera (la pantalla tiene una
 *  parte concedible por función y otra que se abre con una acción).
 *
 * Orden: se toma la primera entrada cuyo `prefix` matchea (`===` o `/…`; con
 * `exact: true` solo `===`), así que lo específico va antes que lo general
 * (`/vacaciones/aprobaciones` antes que `/vacaciones`).
 *
 * Regla al agregar un módulo o pantalla: seed en el catálogo (migración) +
 * `well_known_permissions.py`/`well_known_features.py` + entrada acá + `can()`
 * en los botones de mutación. Ver ARCHITECTURE_GUIDE.md §8. */

export interface RequiredPermission {
  module: string;
  action: string;
}

interface RouteRule {
  prefix: string;
  /** Acciones: alcanza con una. Vacío si la ruta se rige solo por `feature`. */
  anyOf?: RequiredPermission[];
  /** Función concedible por usuario (clave de `module_feature`). */
  feature?: string;
  /** Solo la ruta exacta, no sus sub-rutas (para un hub cuya raíz pide más
   * permiso que sus hijas). */
  exact?: boolean;
}

const p = (module: string, action: string): RequiredPermission => ({ module, action });

export const ROUTE_RULES: readonly RouteRule[] = [
  // Módulo admin, ítem "Usuarios" (cuentas + permisos). Turnos ya no vive acá (ADR-029).
  { prefix: "/admin", anyOf: [p("admin", "manage")] },

  // Turnos: la grilla y sus coberturas se consultan con view; mutar es manage
  // (gateado por botón, no por ruta).
  { prefix: "/turnos", anyOf: [p("turnos", "view")] },

  // Gestión de Personal. Solicitudes/Aprobaciones son acciones; el resto son
  // funciones concedibles por usuario (ADR-032).
  { prefix: "/vacaciones/solicitudes", anyOf: [p("vacaciones", "manage"), p("vacaciones", "create")] },
  { prefix: "/vacaciones/aprobaciones", anyOf: [p("vacaciones", "manage"), p("vacaciones", "approve")] },
  // Asistencias: el registro (calendario/listado/reportes) es la función; la
  // pestaña "Home office y horario" (solicitudes propias) se abre con create,
  // así un operador entra a pedir home office sin ver el registro del equipo.
  {
    prefix: "/vacaciones/asistencias",
    feature: "vacaciones-asistencias",
    anyOf: [p("vacaciones", "manage"), p("vacaciones", "create")],
  },
  { prefix: "/vacaciones/gestion", feature: "vacaciones-gestion-humana" },
  { prefix: "/vacaciones/reportes", feature: "vacaciones-reportes" },
  { prefix: "/vacaciones/auditoria", feature: "vacaciones-auditoria" },
  { prefix: "/vacaciones/configuracion", feature: "vacaciones-configuracion" },
  { prefix: "/vacaciones", exact: true, feature: "vacaciones-dashboard" },
  { prefix: "/vacaciones", anyOf: [p("vacaciones", "view")] },

  // Contadores: el hub raíz ("Automatización": DB3, proyección, FTP, SDS, ERS…)
  // son todas herramientas cuyos endpoints exigen `contadores.export`.
  { prefix: "/contadores", exact: true, anyOf: [p("contadores", "export")] },
  // Pantallas concedibles por usuario (ADR-032).
  { prefix: "/contadores/coberturas", feature: "contadores-coberturas" },
  { prefix: "/contadores/anexos-pendientes", feature: "contadores-anexos" },
  { prefix: "/contadores/clientes-nuevos", feature: "contadores-clientes-nuevos" },
  // Resto: la página entera se abre con view; las acciones se gatean adentro.
  { prefix: "/contadores", anyOf: [p("contadores", "view")] },
  // Insumos: el apartado "Administración" del submenú (Clientes, Configuración,
  // Estadísticas) es una función concedible por usuario (ADR-032); el backend
  // exige la misma función en esos routers. El resto se abre con view.
  { prefix: "/insumos/clientes", feature: "insumos-administracion" },
  { prefix: "/insumos/configuracion", feature: "insumos-administracion" },
  { prefix: "/insumos/estadisticas", feature: "insumos-administracion" },
  { prefix: "/insumos", anyOf: [p("insumos", "view")] },
  { prefix: "/liquidaciones", anyOf: [p("liquidaciones", "view")] },
  { prefix: "/prestadores/coberturas", feature: "prestadores-coberturas" },
  { prefix: "/prestadores", anyOf: [p("prestadores", "view")] },
  { prefix: "/sla", anyOf: [p("sla", "view")] },
  // Pantalla de primer nivel, fuera del árbol /sla, pero del mismo módulo.
  { prefix: "/incidentes-sin-consultar", anyOf: [p("sla", "view")] },
  { prefix: "/preventivos", anyOf: [p("preventivos", "view")] },
  // Pantalla propia del técnico (cargar/ver sus solicitudes de TV) — solo
  // pide "create", no "view" (esa es la del supervisor con todos los
  // técnicos). Específica antes que la general de abajo.
  { prefix: "/bono-tecnicos/solicitudes", anyOf: [p("bono-tecnicos", "create")] },
  { prefix: "/bono-tecnicos", anyOf: [p("bono-tecnicos", "view")] },
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

/** Acceso a una ruta con los chequeos de la sesión (`can` / `hasFeature` de
 * `useSession()`, que ya contemplan superadmin). */
export interface AccessChecks {
  can: (module: string, action: string) => boolean;
  hasFeature: (feature: string) => boolean;
}

export function canAccessPath(pathname: string, checks: AccessChecks): boolean {
  const rule = ruleForPath(pathname);
  if (!rule) return true;
  if (rule.feature && checks.hasFeature(rule.feature)) return true;
  return (rule.anyOf ?? []).some((perm) => checks.can(perm.module, perm.action));
}

/** Módulo al que pertenece la regla (para el toast de "sin permiso"). */
export function moduleForRule(rule: RouteRule): string {
  if (rule.anyOf && rule.anyOf.length > 0) return rule.anyOf[0].module;
  return rule.feature?.split("-")[0] ?? "";
}
