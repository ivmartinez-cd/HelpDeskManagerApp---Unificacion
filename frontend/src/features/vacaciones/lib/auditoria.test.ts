import { describe, expect, it } from "vitest";
import type { RegistroAuditoria } from "../types/vacaciones";
import { descripcionRegistro, detalleRegistro } from "./auditoria";

function registro(accion: string, entidad: string, metadata: Record<string, unknown>): RegistroAuditoria {
  return { id: "1", accion, entidad, entidadId: null, usuarioEmail: null, metadata, createdAt: "2026-10-01T12:00:00Z" };
}

describe("descripción de un registro de auditoría", () => {
  it("describe solicitudes y bajas con empleado y rango dd/mm", () => {
    const m = { employee: "Ana Pérez", startDate: "2026-12-28", endDate: "2027-01-03" };
    expect(descripcionRegistro(registro("APPROVE", "VacationRequest", m))).toBe(
      "Aprobó solicitud de Ana Pérez (28/12–03/01)",
    );
    expect(descripcionRegistro(registro("DELETE", "Absence", m))).toBe("Eliminó baja de Ana Pérez (28/12–03/01)");
  });

  it("omite el rango si falta alguna de las dos fechas", () => {
    expect(descripcionRegistro(registro("CREATE", "Absence", { employee: "Ana", startDate: "2026-01-01" }))).toBe(
      "Creó baja de Ana",
    );
  });

  it("describe empleados, sectores, cargos y feriados", () => {
    expect(descripcionRegistro(registro("UPDATE", "Employee", { employee: "Ana" }))).toBe("Editó empleado: Ana");
    expect(descripcionRegistro(registro("CREATE", "Department", { name: "Soporte" }))).toBe("Creó sector: Soporte");
    expect(descripcionRegistro(registro("DELETE", "Position", { name: "TL" }))).toBe("Eliminó cargo: TL");
    expect(
      descripcionRegistro(registro("CREATE", "Holiday", { name: "Día de la Bandera", date: "2026-06-20" })),
    ).toBe("Creó feriado: Día de la Bandera (2026-06-20)");
  });

  it("la importación de feriados informa cantidad y año, con ? si falta la cantidad", () => {
    expect(descripcionRegistro(registro("IMPORT", "Holiday", { count: 19, year: 2026 }))).toBe(
      "Importó 19 feriados de 2026",
    );
    expect(descripcionRegistro(registro("IMPORT", "Holiday", {}))).toBe("Importó ? feriados de ");
  });

  it("lista los campos cambiados de la configuración", () => {
    expect(descripcionRegistro(registro("UPDATE", "SystemConfig", { changes: ["dias", "tope"] }))).toBe(
      "Actualizó la configuración: dias, tope",
    );
    expect(descripcionRegistro(registro("UPDATE", "SystemConfig", {}))).toBe("Actualizó la configuración: ");
  });

  it("para entidades sin caso propio usa el verbo o la acción cruda y la etiqueta de la entidad", () => {
    expect(descripcionRegistro(registro("UPDATE", "User", {}))).toBe("Editó Usuario");
    expect(descripcionRegistro(registro("LOGIN", "User", {}))).toBe("LOGIN Usuario");
    expect(descripcionRegistro(registro("CREATE", "Desconocida", {}))).toBe("Creó Desconocida");
  });

  it("ignora metadata que no es texto en vez de mostrar [object Object]", () => {
    expect(descripcionRegistro(registro("UPDATE", "Employee", { employee: 42 }))).toBe("Editó empleado: ");
  });
});

describe("detalle de un registro de auditoría", () => {
  it("traduce las claves conocidas, conserva las desconocidas y descarta vacíos", () => {
    const detalle = detalleRegistro(
      registro("UPDATE", "SystemConfig", {
        employee: "Ana",
        days: 0,
        changes: ["a", "b"],
        extra: true,
        comment: "",
        status: null,
        email: undefined,
      }),
    );
    expect(detalle).toEqual([
      { clave: "Empleado", valor: "Ana" },
      { clave: "Días", valor: "0" },
      { clave: "Cambios", valor: "a, b" },
      { clave: "extra", valor: "true" },
    ]);
  });
});
