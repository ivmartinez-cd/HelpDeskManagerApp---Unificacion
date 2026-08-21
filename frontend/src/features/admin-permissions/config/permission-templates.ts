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
}

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
];

const OPERADOR: readonly (readonly [string, string])[] = [
  ...VIEW_ALL,
  ["contadores", "export"],
  ["insumos", "create"],
  ["insumos", "update"],
  ["sla", "update"],
  ["preventivos", "update"],
  ["vacaciones", "create"],
];

const TEAM_LEADER: readonly (readonly [string, string])[] = [
  ...OPERADOR,
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
      "Mesa de ayuda: contadores (herramientas), insumos (solicitudes), SLA, preventivos y sus propias vacaciones.",
    grants: OPERADOR,
  },
  {
    key: "team-leader",
    label: "Team leader",
    description:
      "Operador + administrar contadores y turnos, prestadores, liquidaciones (aprobar/anular/CSV) y vacaciones del equipo.",
    grants: TEAM_LEADER,
  },
  {
    key: "administrador",
    label: "Administrador",
    description: "Team leader + Configuración (usuarios y permisos).",
    grants: [...TEAM_LEADER, ["admin", "manage"]],
  },
];
