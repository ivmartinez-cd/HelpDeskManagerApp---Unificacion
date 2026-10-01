import { afterEach, describe, expect, it, vi } from "vitest";
import type { CalendarEvent, CoberturaEvento } from "../types/calendario";
import {
  cleanTitle, coberturaBadgeText, diasDeAtraso, formatFechaCobertura, formatPillText, getEventPillClassName,
  getMonthDateRange, getMonthNameCapitalized, getPillVisual, operadorEfectivo, textoAtraso, textoDesdeSync,
} from "./calendario-format";

const evento = (over: Partial<CalendarEvent> = {}): CalendarEvent =>
  ({ id: "e1", title: "", start: "2026-09-01", all_day: true, ...over }) as CalendarEvent;

const cobertura = (over: Partial<CoberturaEvento> = {}): CoberturaEvento => ({
  override_id: "o1", operador_ausente_id: "op1", operador_ausente_nombre: "Ana Pérez",
  operador_reemplazante_id: "op2", operador_reemplazante_nombre: "Juan Carlos López",
  operador_reemplazante_color: "#123456", vigente_desde: "2026-09-01", vigente_hasta: "2026-09-10",
  alcance_total: true, ...over,
});

afterEach(() => {
  vi.useRealTimers();
});

describe("rango del mes del calendario", () => {
  it("devuelve del primero al último día del mes actual", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-02-15T12:00:00-03:00"));
    expect(getMonthDateRange()).toEqual({ startStr: "2026-02-01", endStr: "2026-02-28" });
  });

  it("cruza de año al desplazarse meses", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-15T12:00:00-03:00"));
    expect(getMonthDateRange(-1)).toEqual({ startStr: "2025-12-01", endStr: "2025-12-31" });
    vi.setSystemTime(new Date("2026-12-15T12:00:00-03:00"));
    expect(getMonthDateRange(1)).toEqual({ startStr: "2027-01-01", endStr: "2027-01-31" });
  });

  it("titula el mes con mayúscula inicial y año, y deja tal cual lo que no tiene guiones", () => {
    expect(getMonthNameCapitalized("2026-09-01")).toBe("Septiembre 2026");
    expect(getMonthNameCapitalized("202609")).toBe("202609");
  });
});

describe("texto del pill de un evento", () => {
  it("limpia etiquetas HTML del título", () => {
    expect(cleanTitle("  <b>Cliente</b> X ")).toBe("Cliente X");
    expect(cleanTitle(null)).toBe("");
  });

  it("normaliza '[Tipo]:' a '(Tipo)'", () => {
    expect(formatPillText(evento({ title: "[Facturación]: Acme" }))).toBe("(Facturación) Acme");
    expect(formatPillText(evento({ title: "[Vencimiento] Beta" }))).toBe("(Vencimiento) Beta");
  });

  it("antepone el tipo de evento cuando el título no lo trae", () => {
    expect(formatPillText(evento({ title: "Acme", string_tipo_evento: "Entrega" }))).toBe("(Entrega) Acme");
    expect(formatPillText(evento({ title: "(Otro) Acme", string_tipo_evento: "Entrega" }))).toBe("(Otro) Acme");
  });

  it("sin título usa el cliente como facturación", () => {
    expect(formatPillText(evento({ title: "<br>", cliente: "Acme" }))).toBe("(Facturación) Acme");
    expect(formatPillText(evento({ title: "" }))).toBe("Facturación");
  });
});

describe("color del pill", () => {
  it("respeta el color de Gestión y si no, cae al color institucional por tipo", () => {
    expect(getEventPillClassName(evento({ background_color: "#ff0000" }))).toContain("text-white border");
    expect(getEventPillClassName(evento({ string_tipo_evento: "Facturación" }))).toContain("bg-brand-orange");
    expect(getEventPillClassName(evento({ title: "Vencimiento contrato" }))).toContain("bg-brand-gray ");
    expect(getEventPillClassName(evento({ title: "Otra cosa" }))).toContain("bg-brand-gray/50");
  });

  it("en modo efectivo un evento cubierto toma el color del reemplazante, o naranja si no tiene", () => {
    const cubierto = evento({ background_color: "#ff0000", cobertura: cobertura() });
    expect(getPillVisual(cubierto, "efectivo").style?.backgroundColor).toContain("#123456");
    expect(getPillVisual(cubierto, "real").style?.backgroundColor).toContain("#ff0000");
    const sinColor = evento({ cobertura: cobertura({ operador_reemplazante_color: null }) });
    expect(getPillVisual(sinColor, "efectivo")).toEqual({ className: "bg-brand-orange text-white hover:bg-brand-orange-hover" });
  });

  it("el badge de cobertura usa las iniciales del reemplazante según el modo", () => {
    expect(coberturaBadgeText(cobertura(), "efectivo")).toBe("CUBIERTO POR JL");
    expect(coberturaBadgeText(cobertura(), "real")).toBe("↩ JL cubre");
  });
});

describe("operador efectivo de un evento", () => {
  const operadores = [{ id: "op1", nombre: "Ana Pérez", color: "#aaa" }];

  it("con cobertura vigente muestra al reemplazante", () => {
    const op = operadorEfectivo(evento({ operador_id: "op1", cobertura: cobertura() }), operadores);
    expect(op).toMatchObject({ id: "op2", nombre: "Juan Carlos López", color: "#123456" });
    expect(op?.cobertura).not.toBeNull();
  });

  it("sin cobertura muestra al operador real, con su id si no está en el catálogo", () => {
    expect(operadorEfectivo(evento({ operador_id: "op1" }), operadores)).toEqual({
      id: "op1", nombre: "Ana Pérez", color: "#aaa", cobertura: null,
    });
    expect(operadorEfectivo(evento({ operador_id: "op9" }), operadores)).toEqual({
      id: "op9", nombre: "op9", color: null, cobertura: null,
    });
    expect(operadorEfectivo(evento(), operadores)).toBeNull();
  });
});

describe("atrasos y sincronización", () => {
  it("cuenta días de atraso entre fechas puras, ignorando la hora del evento", () => {
    expect(diasDeAtraso("2026-09-28T10:00:00", "2026-10-01")).toBe(3);
    expect(diasDeAtraso("2026-10-01", "2026-10-01")).toBe(0);
    expect(diasDeAtraso("2026-02-28", "2026-03-01")).toBe(1);
  });

  it("describe el atraso en singular y plural", () => {
    expect(textoAtraso(1)).toBe("hace 1 día");
    expect(textoAtraso(4)).toBe("hace 4 días");
  });

  it("describe hace cuánto se sincronizó en minutos, horas o días", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-01T12:00:00Z"));
    expect(textoDesdeSync(null)).toBe("nunca sincronizado");
    expect(textoDesdeSync("2026-10-01T11:59:30Z")).toBe("actualizado recién");
    expect(textoDesdeSync("2026-10-01T11:15:00Z")).toBe("actualizado hace 45 min");
    expect(textoDesdeSync("2026-10-01T09:00:00Z")).toBe("actualizado hace 3 h");
    expect(textoDesdeSync("2026-09-29T11:00:00Z")).toBe("actualizado hace 2 d");
  });

  it("formatea la fecha de cobertura sin correrla un día ni dejar puntos", () => {
    // El texto exacto depende de los datos de Intl ("15 ago 2026" en el navegador,
    // "15 de ago de 2026" en Node).
    expect(formatFechaCobertura("2026-08-15")).toMatch(/^15 (de )?ago (de )?2026$/);
    expect(formatFechaCobertura("2026-08-01")).not.toContain(".");
  });
});
