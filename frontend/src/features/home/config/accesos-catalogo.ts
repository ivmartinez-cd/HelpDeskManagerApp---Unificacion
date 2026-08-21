import {
  BarChart3,
  CalendarClock,
  CalendarDays,
  ClipboardCheck,
  ClipboardList,
  FileSearch,
  FileText,
  Gauge,
  History,
  LayoutDashboard,
  Monitor,
  MonitorOff,
  ReceiptText,
  ScrollText,
  UserRoundCheck,
  Users,
  UserPlus,
  type LucideIcon,
} from "lucide-react";

export interface AccesoDirecto {
  href: string;
  label: string;
  icon: LucideIcon;
  /** `module.key` de `useSession().modules` — filtra el acceso si el
   * usuario no tiene el módulo habilitado. */
  moduleKey: string;
}

/** Whitelist de rutas trackeables como "acceso directo" (fuente de verdad
 * también para el `POST` de tracking de `route-tracker.tsx`) y catálogo de
 * label/ícono para el ranking que devuelve el backend, que solo conoce
 * `route`/`moduleKey`. Deliberadamente NO incluye pantallas de
 * configuración/auditoría (no son "lo que más se usa" del día a día). */
export const ACCESOS_CATALOGO: AccesoDirecto[] = [
  { href: "/contadores/calendario", label: "Calendario", icon: CalendarDays, moduleKey: "contadores" },
  { href: "/contadores/coberturas", label: "Coberturas", icon: UserRoundCheck, moduleKey: "contadores" },
  { href: "/contadores/equipos-sin-real", label: "Sin contador real", icon: Gauge, moduleKey: "contadores" },
  { href: "/contadores/anexos-pendientes", label: "Anexos sin facturar", icon: ReceiptText, moduleKey: "contadores" },
  { href: "/contadores/clientes-nuevos", label: "Clientes nuevos", icon: UserPlus, moduleKey: "contadores" },
  { href: "/insumos", label: "Solicitudes", icon: ClipboardList, moduleKey: "insumos" },
  { href: "/insumos/historial", label: "Historial de pedidos", icon: History, moduleKey: "insumos" },
  { href: "/insumos/equipos-nuevos", label: "Equipos sin registrar", icon: Monitor, moduleKey: "insumos" },
  { href: "/insumos/equipos-offline", label: "Equipos offline", icon: MonitorOff, moduleKey: "insumos" },
  { href: "/insumos/clientes", label: "Clientes de insumos", icon: Users, moduleKey: "insumos" },
  { href: "/insumos/estadisticas", label: "Estadísticas de insumos", icon: BarChart3, moduleKey: "insumos" },
  { href: "/prestadores", label: "Prestadores Asignados", icon: Users, moduleKey: "prestadores" },
  { href: "/prestadores/coberturas", label: "Coberturas ST", icon: UserRoundCheck, moduleKey: "prestadores" },
  { href: "/liquidaciones", label: "Resumen Liquidación", icon: LayoutDashboard, moduleKey: "liquidaciones" },
  { href: "/liquidaciones/lista", label: "Liquidaciones", icon: FileText, moduleKey: "liquidaciones" },
  { href: "/sla", label: "Resumen SLA", icon: Gauge, moduleKey: "sla" },
  { href: "/sla/pendientes-a-cerrar", label: "Pendientes a Cerrar", icon: CalendarClock, moduleKey: "sla" },
  { href: "/preventivos", label: "Preventivos por zona", icon: CalendarClock, moduleKey: "preventivos" },
  { href: "/analisis-log-hp", label: "Análisis Logs HP", icon: FileSearch, moduleKey: "analisis-log-hp" },
  { href: "/vacaciones", label: "Dashboard Vacaciones", icon: LayoutDashboard, moduleKey: "vacaciones" },
  { href: "/vacaciones/solicitudes", label: "Solicitudes de vacaciones", icon: ScrollText, moduleKey: "vacaciones" },
  { href: "/vacaciones/aprobaciones", label: "Aprobaciones", icon: ClipboardCheck, moduleKey: "vacaciones" },
];

/** Respaldo fijo mientras no hay suficientes visitas registradas para armar
 * un ranking real (o para completar hasta 6 si el ranking trae menos). */
export const ACCESOS_RESPALDO: readonly string[] = [
  "/contadores/calendario",
  "/contadores/anexos-pendientes",
  "/insumos",
  "/prestadores",
  "/sla/pendientes-a-cerrar",
  "/liquidaciones/lista",
];

export function findAcceso(href: string): AccesoDirecto | undefined {
  return ACCESOS_CATALOGO.find((a) => a.href === href);
}
