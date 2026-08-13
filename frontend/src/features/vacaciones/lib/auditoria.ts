/** Mapeo del vocabulario del log (acciones/entidades legacy en inglés) a las
 * etiquetas en castellano del handoff, y armado de la descripción a partir de
 * la metadata que escriben los use cases del backend. */

import type { RegistroAuditoria } from "../types/vacaciones";

export const ACCION_LABEL: Record<string, { label: string; bg: string; color: string }> = {
  CREATE: { label: "Creación", bg: "rgba(37,99,235,.12)", color: "#3b82f6" },
  UPDATE: { label: "Edición", bg: "rgba(217,119,6,.14)", color: "#d97706" },
  DELETE: { label: "Eliminación", bg: "rgba(220,38,38,.12)", color: "#ef4444" },
  APPROVE: { label: "Aprobación", bg: "rgba(5,150,105,.14)", color: "#10b981" },
  REJECT: { label: "Rechazo", bg: "rgba(220,38,38,.12)", color: "#ef4444" },
  IMPORT: { label: "Importación", bg: "rgba(37,99,235,.12)", color: "#3b82f6" },
  LOGIN: { label: "Login", bg: "rgba(100,116,139,.14)", color: "#94a3b8" },
  RESET_PASSWORD: { label: "Reset clave", bg: "rgba(100,116,139,.14)", color: "#94a3b8" },
};

export const ENTIDAD_LABEL: Record<string, string> = {
  VacationRequest: "Solicitud",
  Absence: "Baja",
  Employee: "Empleado",
  Department: "Sector",
  Position: "Cargo",
  Holiday: "Feriado",
  SystemConfig: "Configuración",
  User: "Usuario",
};

const str = (v: unknown): string => (typeof v === "string" ? v : "");

function rango(m: Record<string, unknown>): string {
  const desde = str(m.startDate);
  const hasta = str(m.endDate);
  if (!desde || !hasta) return "";
  const f = (iso: string) => iso.slice(8, 10) + "/" + iso.slice(5, 7);
  return ` (${f(desde)}–${f(hasta)})`;
}

const VERBOS: Record<string, string> = {
  CREATE: "Creó",
  UPDATE: "Editó",
  DELETE: "Eliminó",
  APPROVE: "Aprobó",
  REJECT: "Rechazó",
};

export function descripcionRegistro(r: RegistroAuditoria): string {
  const m = r.metadata;
  const verbo = VERBOS[r.accion] ?? r.accion;
  switch (r.entidad) {
    case "VacationRequest":
      return `${verbo} solicitud de ${str(m.employee)}${rango(m)}`;
    case "Absence":
      return `${verbo} baja de ${str(m.employee)}${rango(m)}`;
    case "Employee":
      return `${verbo} empleado: ${str(m.employee)}`;
    case "Department":
      return `${verbo} sector: ${str(m.name)}`;
    case "Position":
      return `${verbo} cargo: ${str(m.name)}`;
    case "Holiday":
      if (r.accion === "IMPORT") {
        return `Importó ${String(m.count ?? "?")} feriados de ${String(m.year ?? "")}`;
      }
      return `${verbo} feriado: ${str(m.name)} (${str(m.date)})`;
    case "SystemConfig": {
      const cambios = Array.isArray(m.changes) ? m.changes.join(", ") : "";
      return `Actualizó la configuración: ${cambios}`;
    }
    default:
      return `${verbo} ${ENTIDAD_LABEL[r.entidad] ?? r.entidad}`;
  }
}

const CLAVE_LABEL: Record<string, string> = {
  employee: "Empleado",
  email: "Email",
  startDate: "Desde",
  endDate: "Hasta",
  previousStart: "Desde (antes)",
  previousEnd: "Hasta (antes)",
  days: "Días",
  type: "Tipo",
  status: "Estado",
  comment: "Comentario",
  name: "Nombre",
  date: "Fecha",
  year: "Año",
  count: "Cantidad",
  changes: "Cambios",
};

export function detalleRegistro(r: RegistroAuditoria): { clave: string; valor: string }[] {
  return Object.entries(r.metadata)
    .filter(([, v]) => v !== null && v !== undefined && v !== "")
    .map(([k, v]) => ({
      clave: CLAVE_LABEL[k] ?? k,
      valor: Array.isArray(v) ? v.join(", ") : String(v),
    }));
}
