import { NUMBER_FIELD_SPECS } from "./config-fields";
import {
  NUMERIC_CONFIG_KEYS,
  parseEmails,
  parseIntegerField,
  type ConfigFieldKey,
  type ConfigFormState,
} from "./config-form";

/** Validación client-side del formulario de Configuración.
 *
 * Es un espejo de `domain/services/settings_validation.py`: mismos rangos y
 * mismos mensajes, para que el operario vea el problema en el campo en vez de
 * mandar el PUT y leer un error genérico arriba de todo. El backend igual
 * valida (y su error se muestra tal cual si algo se escapa) — esto no lo
 * reemplaza, lo adelanta.
 */

export type ConfigErrors = Partial<Record<ConfigFieldKey, string>>;

/** Mismo regex que usa el backend (`_EMAIL_RE`). */
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export function validateConfigForm(form: ConfigFormState): ConfigErrors {
  const errors: ConfigErrors = {};

  for (const key of NUMERIC_CONFIG_KEYS) {
    const spec = NUMBER_FIELD_SPECS[key];
    if (!spec) continue;
    const value = parseIntegerField(form[key]);
    if (value === null) {
      errors[key] = "Ingresá un número entero.";
      continue;
    }
    if (value < spec.min || value > spec.max) {
      errors[key] = spec.rangeError ?? `El valor debe estar entre ${spec.min} y ${spec.max}.`;
    }
  }

  applyThresholdOrder(form, errors);
  applyWorkHourOrder(form, errors);
  applyEmails(form, errors);
  applyOpsAlertEmails(form, errors);

  return errors;
}

/** El orden de los umbrales solo se chequea si los tres parsean: si alguno ya
 * tiene error de formato, comparar contra `null` daría un segundo mensaje
 * confuso en un campo que está bien. */
function applyThresholdOrder(form: ConfigFormState, errors: ConfigErrors): void {
  const critical = parseIntegerField(form.thresholdCritical);
  const urgent = parseIntegerField(form.thresholdUrgent);
  const warning = parseIntegerField(form.thresholdWarning);
  if (critical === null || urgent === null || warning === null) return;
  if (critical >= urgent) {
    errors.thresholdCritical ??= "El umbral Crítico debe ser menor que Urgente.";
  }
  if (urgent >= warning) {
    errors.thresholdUrgent ??= "El umbral Urgente debe ser menor que Atención.";
  }
}

function applyWorkHourOrder(form: ConfigFormState, errors: ConfigErrors): void {
  const start = parseIntegerField(form.alertWorkHourStart);
  const end = parseIntegerField(form.alertWorkHourEnd);
  if (start === null || end === null) return;
  if (start >= end) {
    errors.alertWorkHourStart ??= "La hora de inicio debe ser menor que la hora de fin.";
  }
}

function applyEmails(form: ConfigFormState, errors: ConfigErrors): void {
  const invalid = parseEmails(form.logisticsMailTo).filter((email) => !EMAIL_RE.test(email));
  if (invalid.length > 0) {
    errors.logisticsMailTo = `Email(s) inválido(s) en logística: ${invalid.join(", ")}`;
  }
}

/** A diferencia de logística, este campo nunca puede quedar vacío — sin un
 * destinatario, una falla real del sistema no le llega a nadie. Mismo
 * resguardo que `settings_validation._validate_ops_alert_emails` en el
 * backend (incidente real 2026-08-12, ver CLAUDE.md). */
function applyOpsAlertEmails(form: ConfigFormState, errors: ConfigErrors): void {
  const emails = parseEmails(form.opsAlertMailTo);
  if (emails.length === 0) {
    errors.opsAlertMailTo = "Tiene que haber al menos un email de alertas técnicas.";
    return;
  }
  const invalid = emails.filter((email) => !EMAIL_RE.test(email));
  if (invalid.length > 0) {
    errors.opsAlertMailTo = `Email(s) inválido(s) en alertas técnicas: ${invalid.join(", ")}`;
  }
}

export function hasErrors(errors: ConfigErrors): boolean {
  return Object.keys(errors).length > 0;
}
