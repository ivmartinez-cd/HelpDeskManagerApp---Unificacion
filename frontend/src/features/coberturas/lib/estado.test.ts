import { afterEach, describe, expect, it, vi } from "vitest";
import type { Cobertura } from "../types/coberturas";
import { deriveEstado, formatFechaCorta, hoyIso } from "./estado";

afterEach(() => {
  vi.useRealTimers();
});

const cobertura: Cobertura = {
  id: "c1",
  ausenteId: "u1",
  ausenteNombre: "Ana",
  reemplazanteId: "u2",
  reemplazanteNombre: "Beto",
  desde: "2026-10-05",
  hasta: "2026-10-09",
  alcanceTotal: true,
  alcanceItems: [],
  estado: "ACTIVA",
  motivo: null,
  intercambioId: null,
};

describe("estado derivado de una cobertura", () => {
  it("es programada antes de desde, activa entre desde y hasta inclusive y vencida después", () => {
    expect(deriveEstado(cobertura, "2026-10-04")).toBe("programada");
    expect(deriveEstado(cobertura, "2026-10-05")).toBe("activa");
    expect(deriveEstado(cobertura, "2026-10-09")).toBe("activa");
    expect(deriveEstado(cobertura, "2026-10-10")).toBe("vencida");
  });

  it("cancelada gana sobre cualquier fecha", () => {
    expect(deriveEstado({ ...cobertura, estado: "CANCELADA" }, "2026-10-06")).toBe("cancelada");
  });

  it("sin fecha explícita usa el día local de Argentina, no el UTC", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-10T02:59:00Z")); // 09/10 23:59 en Argentina
    expect(hoyIso()).toBe("2026-10-09");
    expect(deriveEstado(cobertura)).toBe("activa");
  });
});

describe("fecha corta de coberturas", () => {
  it("no retrocede un día en huso negativo y saca los puntos de la abreviatura", () => {
    // Salida real del ICU de Node en el contenedor (es-AR).
    expect(formatFechaCorta("2026-08-15")).toBe("15 de ago de 2026");
    expect(formatFechaCorta("2026-10-01")).toBe("01 de oct de 2026");
  });
});
