import { describe, expect, it } from "vitest";
import { aHhmm, completarAlDesenfocar, digitosDeRaw, formatearDigitos } from "./time-hhmm";

describe("input de hora HH:MM", () => {
  it("se queda con hasta 4 dígitos de lo tipeado", () => {
    expect(digitosDeRaw("1a2:3b45")).toBe("1234");
  });

  it("clampea horas y minutos e inserta los dos puntos al pasar a minutos", () => {
    expect(formatearDigitos("2")).toBe("2");
    expect(formatearDigitos("29")).toBe("23");
    expect(formatearDigitos("123")).toBe("12:3");
    expect(formatearDigitos("2399")).toBe("23:59");
  });

  it("al desenfocar completa con cero la parte a medio tipear", () => {
    expect(completarAlDesenfocar("9")).toBe("09");
    expect(completarAlDesenfocar("125")).toBe("1205");
  });

  it("solo da un HH:MM final con los 4 dígitos", () => {
    expect(aHhmm("123")).toBe("");
    expect(aHhmm("0745")).toBe("07:45");
    expect(aHhmm("9999")).toBe("23:59");
  });
});
