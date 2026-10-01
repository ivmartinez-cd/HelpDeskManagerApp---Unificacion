import { afterEach, describe, expect, it, vi } from "vitest";
import { formatAntiguedad, formatFecha, formatFechaCorta, formatRango, hoyIso, iniciales } from "./fechas";

afterEach(() => {
  vi.useRealTimers();
});

describe("formatos de fecha de vacaciones", () => {
  it("formatea la fecha ISO sin pasar por Date", () => {
    expect(formatFechaCorta("2026-03-05")).toBe("05/03");
    expect(formatFecha("2026-03-05")).toBe("05/03/2026");
  });

  it("describe un rango con mes abreviado, aun entre años", () => {
    expect(formatRango("2026-10-05", "2026-10-09")).toBe("5 oct – 9 oct");
    expect(formatRango("2026-12-28", "2027-01-03")).toBe("28 dic – 3 ene");
  });

  it("redondea la antigüedad hacia abajo y la describe en singular o plural", () => {
    expect(formatAntiguedad(0)).toBe("menos de 1 año");
    expect(formatAntiguedad(0.99)).toBe("menos de 1 año");
    expect(formatAntiguedad(1.9)).toBe("1 año");
    expect(formatAntiguedad(5.2)).toBe("5 años");
  });

  it("hoy es la fecha local de Argentina, no la UTC", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-01T02:30:00Z")); // 30/09 23:30 en Argentina
    expect(hoyIso()).toBe("2026-09-30");
  });

  it("toma las iniciales de las dos primeras palabras", () => {
    expect(iniciales("  juan   pérez gómez ")).toBe("JP");
    expect(iniciales("Ana")).toBe("A");
    expect(iniciales("")).toBe("");
  });
});
