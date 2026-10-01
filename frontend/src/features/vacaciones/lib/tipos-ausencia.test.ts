import { describe, expect, it } from "vitest";
import { horaCorta, horarioTexto } from "./tipos-ausencia";

describe("horario de un cambio de horario", () => {
  it("recorta los segundos de la hora", () => {
    expect(horaCorta("08:30:00")).toBe("08:30");
    expect(horaCorta("08:30")).toBe("08:30");
  });

  it("muestra el rango solo si están las dos horas", () => {
    expect(horarioTexto({ horaDesde: "08:00:00", horaHasta: "17:00:00" })).toBe("08:00–17:00");
    expect(horarioTexto({ horaDesde: "08:00:00", horaHasta: null })).toBeNull();
    expect(horarioTexto({ horaDesde: null, horaHasta: null })).toBeNull();
  });
});
