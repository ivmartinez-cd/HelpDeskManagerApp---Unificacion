import type { InsumosConfig, InsumosConfigPayload } from "../../types";

/** Estado del formulario de Configuración.
 *
 * Los campos numéricos se guardan como STRING, no como `number`: mientras el
 * operario está tipeando el input pasa por estados intermedios ("", "-", "1e")
 * que como número serían `NaN` y borrarían el valor de la pantalla. Se parsean
 * recién al validar y al armar el payload.
 *
 * `logisticsMailTo` es un `string[]` en la API pero un textarea en la UI (un
 * mail por línea, igual que el legacy) — se convierte en las dos direcciones. */

export type NumericConfigKey =
  | "thresholdCritical"
  | "thresholdUrgent"
  | "thresholdWarning"
  | "autoloadMaxDays"
  | "autoloadMinPercent"
  | "validationWindowHours"
  | "staleDeviceDays"
  | "offlineDeviceHours"
  | "offlineMonitorHours"
  | "offlineOutageMinDevices"
  | "offlineOutageMinPercent"
  | "alertEscalationMinutes"
  | "alertWorkHourStart"
  | "alertWorkHourEnd";

export type BooleanConfigKey = "autoloadEnabled" | "alertWorkHoursEnabled";

export type ConfigFieldKey = NumericConfigKey | BooleanConfigKey | "logisticsMailTo";

export type ConfigFormState = Record<NumericConfigKey, string> &
  Record<BooleanConfigKey, boolean> & { logisticsMailTo: string };

export const NUMERIC_CONFIG_KEYS: readonly NumericConfigKey[] = [
  "thresholdCritical",
  "thresholdUrgent",
  "thresholdWarning",
  "autoloadMaxDays",
  "autoloadMinPercent",
  "validationWindowHours",
  "staleDeviceDays",
  "offlineDeviceHours",
  "offlineMonitorHours",
  "offlineOutageMinDevices",
  "offlineOutageMinPercent",
  "alertEscalationMinutes",
  "alertWorkHourStart",
  "alertWorkHourEnd",
];

export function toFormState(config: InsumosConfig): ConfigFormState {
  const numeric = Object.fromEntries(
    NUMERIC_CONFIG_KEYS.map((key) => [key, String(config[key])]),
  ) as Record<NumericConfigKey, string>;
  return {
    ...numeric,
    autoloadEnabled: config.autoloadEnabled,
    alertWorkHoursEnabled: config.alertWorkHoursEnabled,
    logisticsMailTo: config.logisticsMailTo.join("\n"),
  };
}

/** Acepta separación por saltos de línea, comas o punto y coma — pegar una
 * lista de mails desde Outlook no debería requerir reformatearla a mano. */
export function parseEmails(raw: string): string[] {
  return raw
    .split(/[\n,;]+/)
    .map((email) => email.trim())
    .filter((email) => email !== "");
}

export function parseIntegerField(raw: string): number | null {
  const trimmed = raw.trim();
  if (trimmed === "") return null;
  if (!/^-?\d+$/.test(trimmed)) return null;
  return Number(trimmed);
}

/** Payload del PUT. Solo se llama con un formulario ya validado, así que los
 * enteros parsean; el `?? 0` es para satisfacer al tipo, no un default real
 * (el backend tiene los suyos para campos ausentes). */
export function toPayload(form: ConfigFormState): InsumosConfigPayload {
  const numeric = Object.fromEntries(
    NUMERIC_CONFIG_KEYS.map((key) => [key, parseIntegerField(form[key]) ?? 0]),
  ) as Record<NumericConfigKey, number>;
  return {
    ...numeric,
    autoloadEnabled: form.autoloadEnabled,
    alertWorkHoursEnabled: form.alertWorkHoursEnabled,
    logisticsMailTo: parseEmails(form.logisticsMailTo),
  };
}

export function isDirty(form: ConfigFormState, original: ConfigFormState): boolean {
  return (Object.keys(original) as (keyof ConfigFormState)[]).some(
    (key) => form[key] !== original[key],
  );
}
