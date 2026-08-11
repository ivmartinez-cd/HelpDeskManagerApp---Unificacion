import type { BooleanConfigKey, ConfigFieldKey, NumericConfigKey } from "./config-form";

/** Metadata de los campos reales de `GET/PUT /api/insumos/config` — no hay
 * campos inventados acá: la lista es exactamente la de `ConfigResponse` del
 * backend (17 campos).
 *
 * `min`/`max` y `rangeError` replican **literalmente** las validaciones de
 * `domain/services/settings_validation.py`, con el mismo mensaje en español
 * que devolvería el backend en `{ok:false, error}`. La idea es que el operario
 * vea el problema antes de mandar el PUT, no que el cliente invente reglas
 * propias: si el backend no acota un campo, acá tampoco se acota.
 *
 * Las secciones NO son las 7 del README del handoff (esas son de config por
 * cliente de Contadores, otro módulo): se agruparon por los bloques de
 * validación reales del backend — umbrales, auto-carga, ventana de validación,
 * equipos offline, alertas/horario y logística.
 */

export interface NumberFieldSpec {
  kind: "number";
  key: NumericConfigKey;
  label: string;
  hint?: string;
  /** Unidad que se muestra dentro del input (días, horas, %, minutos). */
  suffix?: string;
  min: number;
  max: number;
  /** Mensaje exacto del backend cuando el valor cae fuera de rango. `null`
   * cuando el backend no valida rango absoluto (solo el orden relativo). */
  rangeError: string | null;
}

export interface BooleanFieldSpec {
  kind: "boolean";
  key: BooleanConfigKey;
  label: string;
  hint?: string;
}

export interface EmailsFieldSpec {
  kind: "emails";
  key: "logisticsMailTo";
  label: string;
  hint?: string;
}

export type ConfigFieldSpec = NumberFieldSpec | BooleanFieldSpec | EmailsFieldSpec;

export interface ConfigSectionSpec {
  id: string;
  title: string;
  description: string;
  fields: readonly ConfigFieldSpec[];
}

/** Los umbrales no tienen rango absoluto en el backend, solo el orden
 * crítico < urgente < atención. El único límite propio del cliente es que sean
 * enteros no negativos (un umbral en días negativos no es un caso de uso, y
 * el backend lo aceptaría en silencio). */
const THRESHOLD_MAX = 999;

export const CONFIG_SECTIONS: readonly ConfigSectionSpec[] = [
  {
    id: "umbrales",
    title: "Umbrales de criticidad",
    description:
      "Días de autonomía restantes de un consumible a partir de los cuales la solicitud se marca con cada nivel. Tienen que ir de menor a mayor.",
    fields: [
      {
        kind: "number",
        key: "thresholdCritical",
        label: "Crítico",
        hint: "Menor que Urgente",
        suffix: "días",
        min: 0,
        max: THRESHOLD_MAX,
        rangeError: null,
      },
      {
        kind: "number",
        key: "thresholdUrgent",
        label: "Urgente",
        hint: "Entre Crítico y Atención",
        suffix: "días",
        min: 0,
        max: THRESHOLD_MAX,
        rangeError: null,
      },
      {
        kind: "number",
        key: "thresholdWarning",
        label: "Atención",
        hint: "Mayor que Urgente",
        suffix: "días",
        min: 0,
        max: THRESHOLD_MAX,
        rangeError: null,
      },
    ],
  },
  {
    id: "autocarga",
    title: "Auto-carga de pedidos",
    description:
      "Creación automática de pedidos en Canal Directo, sin intervención del operario. Los topes son un límite de seguridad: cuanto más amplios, más solicitudes vuelve elegibles el poller de fondo.",
    fields: [
      {
        kind: "boolean",
        key: "autoloadEnabled",
        label: "Auto-carga habilitada",
        hint: "Si está apagada, todos los pedidos los carga un operario a mano.",
      },
      {
        kind: "number",
        key: "autoloadMaxDays",
        label: "Autonomía máxima para auto-cargar",
        hint: "1 a 30",
        suffix: "días",
        min: 1,
        max: 30,
        rangeError: "Los días para auto-carga deben estar entre 1 y 30.",
      },
      {
        kind: "number",
        key: "autoloadMinPercent",
        label: "Nivel máximo del consumible",
        hint: "1 a 100",
        suffix: "%",
        min: 1,
        max: 100,
        rangeError: "El porcentaje para auto-carga debe estar entre 1 y 100.",
      },
    ],
  },
  {
    id: "validacion",
    title: "Ventana de validación",
    description:
      "Cuánto se espera el cambio real del consumible antes de dar el pedido por no validado. Muy corta no da margen a un glitch de lectura; muy larga deja una solicitud real sin cargar.",
    fields: [
      {
        kind: "number",
        key: "validationWindowHours",
        label: "Ventana de validación",
        hint: "1 a 48",
        suffix: "horas",
        min: 1,
        max: 48,
        rangeError: "Las horas de la ventana de validación deben estar entre 1 y 48.",
      },
    ],
  },
  {
    id: "offline",
    title: "Equipos offline",
    description:
      "Cuándo se considera vieja una lectura, cuándo se audita un equipo sin contacto y con qué evidencia se diagnostica una caída general del colector en vez de equipos sueltos.",
    fields: [
      {
        kind: "number",
        key: "staleDeviceDays",
        label: "Lectura vieja",
        hint: "1 a 60",
        suffix: "días",
        min: 1,
        max: 60,
        rangeError: "Los días sin contacto para marcar offline deben estar entre 1 y 60.",
      },
      {
        kind: "number",
        key: "offlineDeviceHours",
        label: "Sin contacto para auditar el equipo",
        hint: "24 a 720",
        suffix: "horas",
        min: 24,
        max: 720,
        rangeError:
          "Las horas sin contacto para auditar equipos offline deben estar entre 24 y 720.",
      },
      {
        kind: "number",
        key: "offlineMonitorHours",
        label: "Sin contacto para sospechar del colector",
        hint: "24 a 720",
        suffix: "horas",
        min: 24,
        max: 720,
        rangeError:
          "Las horas sin contacto para considerar colector caído deben estar entre 24 y 720.",
      },
      {
        kind: "number",
        key: "offlineOutageMinDevices",
        label: "Mínimo de equipos para caída masiva",
        hint: "2 a 100",
        suffix: "equipos",
        min: 2,
        max: 100,
        rangeError: "El mínimo de equipos para detectar una caída masiva debe estar entre 2 y 100.",
      },
      {
        kind: "number",
        key: "offlineOutageMinPercent",
        label: "Mínimo del parque para caída masiva",
        hint: "1 a 100",
        suffix: "%",
        min: 1,
        max: 100,
        rangeError:
          "El porcentaje mínimo para detectar una caída masiva debe estar entre 1 y 100.",
      },
    ],
  },
  {
    id: "alertas",
    title: "Alertas y horario laboral",
    description:
      "Cuánto puede quedar una solicitud sin cargar antes de escalar, y en qué franja horaria corre ese reloj.",
    fields: [
      {
        kind: "number",
        key: "alertEscalationMinutes",
        label: "Escalar alerta después de",
        hint: "5 a 1440",
        suffix: "minutos",
        min: 5,
        max: 1440,
        rangeError:
          "Los minutos para escalar una alerta de pedido sin cargar deben estar entre 5 y 1440.",
      },
      {
        kind: "boolean",
        key: "alertWorkHoursEnabled",
        label: "Escalar solo en horario laboral",
        hint: "Apagado, el reloj de escalamiento corre las 24 horas.",
      },
      {
        kind: "number",
        key: "alertWorkHourStart",
        label: "Hora de inicio",
        hint: "0 a 23, menor que la de fin",
        suffix: "h",
        min: 0,
        max: 23,
        rangeError: "La hora de inicio de horario laboral debe estar entre 0 y 23.",
      },
      {
        kind: "number",
        key: "alertWorkHourEnd",
        label: "Hora de fin",
        hint: "1 a 24, mayor que la de inicio",
        suffix: "h",
        min: 1,
        max: 24,
        rangeError: "La hora de fin de horario laboral debe estar entre 1 y 24.",
      },
    ],
  },
  {
    id: "logistica",
    title: "Notificaciones de logística",
    description:
      "Destinatarios de los avisos de logística. Un mail por línea (también se acepta separado por comas).",
    fields: [
      {
        kind: "emails",
        key: "logisticsMailTo",
        label: "Emails de logística",
        hint: "Vacío = no se envían avisos",
      },
    ],
  },
];

/** Índice campo → sección, para poder abrir y resaltar la sección que tiene
 * el error que devolvió el backend o la validación local. */
export const SECTION_BY_FIELD: Readonly<Record<ConfigFieldKey, string>> = Object.fromEntries(
  CONFIG_SECTIONS.flatMap((section) => section.fields.map((field) => [field.key, section.id])),
) as Record<ConfigFieldKey, string>;

export const NUMBER_FIELD_SPECS: Readonly<Partial<Record<NumericConfigKey, NumberFieldSpec>>> =
  Object.fromEntries(
    CONFIG_SECTIONS.flatMap((section) =>
      section.fields.filter((field): field is NumberFieldSpec => field.kind === "number"),
    ).map((field) => [field.key, field]),
  ) as Partial<Record<NumericConfigKey, NumberFieldSpec>>;
