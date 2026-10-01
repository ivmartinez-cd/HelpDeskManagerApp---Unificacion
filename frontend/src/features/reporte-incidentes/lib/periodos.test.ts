import { describe, expect, it } from "vitest";
import {
  MAX_MESES_RANGO,
  acotarMeses,
  etiquetaDia,
  etiquetaPeriodo,
  formatearEntero,
  mesesEntre,
  periodosRecientes,
} from "./periodos";

describe("períodos AAAA-MM del reporte de incidentes", () => {
  it("etiqueta el período con el nombre del mes y el año", () => {
    expect(etiquetaPeriodo("2026-01")).toBe("Enero 2026");
    expect(etiquetaPeriodo("2025-12")).toBe("Diciembre 2025");
  });

  it("lista los períodos recientes del más nuevo al más viejo, cruzando el año", () => {
    expect(periodosRecientes(3, new Date(2026, 1, 15))).toEqual(["2026-02", "2026-01", "2025-12"]);
  });

  it("por defecto ofrece el rango máximo de 24 meses", () => {
    const lista = periodosRecientes(undefined, new Date(2026, 9, 1));
    expect(lista).toHaveLength(MAX_MESES_RANGO);
    expect(lista[0]).toBe("2026-10");
    expect(lista.at(-1)).toBe("2024-11");
  });

  it("cuenta los meses entre dos períodos de forma inclusiva", () => {
    expect(mesesEntre("2026-03", "2026-03")).toBe(1);
    expect(mesesEntre("2025-11", "2026-02")).toBe(4);
  });

  it("acota la cantidad de meses entre 1 y 24, descartando valores inválidos", () => {
    expect(acotarMeses(6)).toBe(6);
    expect(acotarMeses(3.9)).toBe(3);
    expect(acotarMeses(30)).toBe(24);
    expect(acotarMeses(0)).toBe(1);
    expect(acotarMeses(-2)).toBe(1);
    expect(acotarMeses(Number.NaN)).toBe(1);
    expect(acotarMeses(Number.POSITIVE_INFINITY)).toBe(1);
  });

  it("formatea enteros con punto de miles", () => {
    expect(formatearEntero(1234567)).toBe("1.234.567");
  });

  it("la etiqueta del día lleva el mes solo si el rango abarca varios meses", () => {
    expect(etiquetaDia("2026-06-10", true)).toBe("10/06");
    expect(etiquetaDia("2026-06-10", false)).toBe("10");
  });
});
