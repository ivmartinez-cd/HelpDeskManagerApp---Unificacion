import { afterEach, describe, expect, it, vi } from "vitest";
import { nivelEspera, sincronizacionVencida, textoEspera } from "./espera";

afterEach(() => {
  vi.useRealTimers();
});

describe("semáforo de espera de WATI", () => {
  it("pasa a atención a los 15 min y a crítico a los 60", () => {
    expect(nivelEspera(14)).toBe("ok");
    expect(nivelEspera(15)).toBe("atencion");
    expect(nivelEspera(60)).toBe("critico");
  });

  it("describe la espera en minutos u horas", () => {
    expect(textoEspera(0)).toBe("recién");
    expect(textoEspera(45)).toBe("hace 45 min");
    expect(textoEspera(120)).toBe("hace 2 h");
    expect(textoEspera(135)).toBe("hace 2 h 15 min");
  });

  it("marca vencida la sincronización de más de 10 minutos o la que nunca ocurrió", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-01T12:00:00Z"));
    expect(sincronizacionVencida(null)).toBe(true);
    expect(sincronizacionVencida("2026-10-01T11:55:00Z")).toBe(false);
    expect(sincronizacionVencida("2026-10-01T11:45:00Z")).toBe(true);
  });
});
