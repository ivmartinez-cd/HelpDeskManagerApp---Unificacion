import { afterEach, describe, expect, it, vi } from "vitest";
import { deriveEstadoVariante, formatDiaMes, formatFecha, hhmm, hoyIso } from "./variante-estado";

afterEach(() => {
  vi.useRealTimers();
});

describe("estado derivado de una grilla de vacaciones", () => {
  const variante = { estado: "ACTIVA" as const, desde: "2026-10-05", hasta: "2026-10-09" };

  it("es programada antes de desde, vigente entre desde y hasta inclusive y vencida después", () => {
    expect(deriveEstadoVariante(variante, "2026-10-04")).toBe("programada");
    expect(deriveEstadoVariante(variante, "2026-10-05")).toBe("vigente");
    expect(deriveEstadoVariante(variante, "2026-10-09")).toBe("vigente");
    expect(deriveEstadoVariante(variante, "2026-10-10")).toBe("vencida");
  });

  it("cancelada gana sobre cualquier fecha", () => {
    expect(deriveEstadoVariante({ ...variante, estado: "CANCELADA" }, "2026-10-06")).toBe("cancelada");
  });

  it("sin fecha explícita usa el día local de Argentina, no el UTC", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-05T01:00:00Z")); // 04/10 22:00 en Argentina
    expect(hoyIso()).toBe("2026-10-04");
    expect(deriveEstadoVariante(variante)).toBe("programada");
  });
});

describe("formatos de la grilla de variantes", () => {
  it("formatea fechas y horas", () => {
    expect(formatDiaMes("2026-08-28")).toBe("28/08");
    expect(formatFecha("2026-08-28")).toBe("28/08/2026");
    expect(hhmm("08:30:00")).toBe("08:30");
  });
});
