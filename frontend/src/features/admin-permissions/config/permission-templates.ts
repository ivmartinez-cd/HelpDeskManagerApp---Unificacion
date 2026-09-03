/** Plantillas por perfil para la grilla de permisos (ADR-029, punto 4).
 *
 * Son un atajo de UI: al aplicarlas se tildan/destildan casillas de la grilla
 * y el admin sigue pudiendo ajustar a mano antes de guardar. No existen roles
 * en el modelo (sigue siendo usuario × módulo × acción, ADR-005): lo que se
 * persiste son grants individuales.
 *
 * Los pares que no existan en el catálogo (`module.actions`) se ignoran al
 * aplicar, así una plantilla no puede conceder algo que la DB no declara.
 * Ajustar estos defaults es una decisión funcional: la fuente de verdad de
 * "qué puede cada perfil" es esta lista, no el código de cada módulo. */

export interface PermissionTemplate {
  key: string;
  label: string;
  description: string;
  /** `[module, action]` */
  grants: readonly (readonly [string, string])[];
  /** Funciones (pantallas/cards) concedibles por usuario (ADR-032), por clave. */
  features?: readonly string[];
}

/** Todas las funciones del catálogo: lo que hoy ve un TL. Si se agrega una
 * función nueva al catálogo, sumarla acá (y al script de backfill). */
const FUNCIONES_TL: readonly string[] = [
  "contadores-coberturas",
  "contadores-anexos",
  "contadores-clientes-nuevos",
  "contadores-sin-real-todos",
  "contadores-card-operadores",
  "insumos-administracion",
  "prestadores-coberturas",
  "prestadores-card-parque",
  "vacaciones-dashboard",
  "vacaciones-asistencias",
  "vacaciones-gestion-humana",
  "vacaciones-reportes",
  "vacaciones-auditoria",
  "vacaciones-configuracion",
  "vacaciones-card-equipo",
];

const VIEW_ALL: readonly (readonly [string, string])[] = [
  ["contadores", "view"],
  ["insumos", "view"],
  ["sla", "view"],
  ["prestadores", "view"],
  ["liquidaciones", "view"],
  ["preventivos", "view"],
  ["analisis-log-hp", "view"],
  ["turnos", "view"],
  ["vacaciones", "view"],
  ["wati", "view"],
];

// Operador: sin Liquidación (ni siquiera consulta) — decisión del usuario
// 2026-08-21 al configurar a los operadores de mesa de ayuda.
const OPERADOR: readonly (readonly [string, string])[] = [
  ...VIEW_ALL.filter(([module]) => module !== "liquidaciones"),
  ["contadores", "export"],
  ["insumos", "create"],
  ["insumos", "update"],
  ["sla", "update"],
  ["preventivos", "update"],
  ["vacaciones", "create"],
];

const TEAM_LEADER: readonly (readonly [string, string])[] = [
  ...OPERADOR,
  ["liquidaciones", "view"],
  ["contadores", "manage"],
  ["insumos", "delete"],
  ["prestadores", "create"],
  ["prestadores", "update"],
  ["prestadores", "delete"],
  ["liquidaciones", "create"],
  ["liquidaciones", "update"],
  ["liquidaciones", "approve"],
  ["liquidaciones", "delete"],
  ["liquidaciones", "export"],
  ["turnos", "manage"],
  ["vacaciones", "approve"],
  ["vacaciones", "manage"],
  ["wati", "update"],
];

export const PERMISSION_TEMPLATES: readonly PermissionTemplate[] = [
  {
    key: "solo-lectura",
    label: "Solo lectura",
    description: "Ver todos los módulos sin editar nada.",
    grants: VIEW_ALL,
  },
  {
    key: "operador",
    label: "Operador",
    description:
      "Mesa de ayuda: contadores (herramientas), insumos (solicitudes, sin Administración), SLA, preventivos y sus propias vacaciones. Sin Liquidación.",
    grants: OPERADOR,
  },
  {
    key: "team-leader",
    label: "Team leader",
    description:
      "Operador + administrar contadores y turnos, prestadores, liquidaciones (aprobar/anular/CSV) y vacaciones del equipo.",
    grants: TEAM_LEADER,
    features: FUNCIONES_TL,
  },
  {
    // No se llama "Administrador" para no confundirlo con el superadmin
    // (flag `is_superadmin`, que la UI muestra como "Administrador" y no
    // necesita grants): esto es un TL que además puede gestionar usuarios.
    key: "tl-configuracion",
    label: "Team leader + Usuarios",
    description: "Team leader + módulo Usuarios (cuentas y permisos). No es superadmin.",
    grants: [...TEAM_LEADER, ["admin", "manage"]],
    features: FUNCIONES_TL,
  },
];
