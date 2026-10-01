import { describe, expect, it } from "vitest";
import { formatARS, formatFecha, formatFechaDia, formatUSD, resumenImportCsv } from "./format";

// Intl separa símbolo e importe con un espacio duro (U+00A0).
const llano = (s: string) => s.replace(/\s/g, " ");

describe("formatos de liquidaciones", () => {
  it("muestra importes en pesos y dólares con formato argentino", () => {
    expect(llano(formatARS(1234567.891))).toBe("$ 1.234.567,89");
    expect(llano(formatARS(0))).toBe("$ 0,00");
    expect(llano(formatUSD(1234.5))).toBe("US$ 1.234,50");
  });

  it("formatea un timestamp con la fecha local, sin ceros a la izquierda", () => {
    expect(formatFecha("2026-08-05T15:00:00Z")).toBe("5/8/2026");
  });

  it("formatea una fecha pura sin correrla un día por el huso de Argentina", () => {
    expect(formatFechaDia("2026-08-01")).toBe("01/08/2026");
  });
});

describe("resumen del import CSV", () => {
  const base = { creados: 0, actualizados: 0, sinCambios: 0, descartadas: 0 };

  it("lista nuevas, actualizadas y sin cambios con singular y plural", () => {
    expect(resumenImportCsv({ ...base, creados: 2, actualizados: 1, sinCambios: 5 }, "tarifa", "tarifas"))
      .toBe("2 tarifas nuevas, 1 actualizada, 5 sin cambios");
    expect(resumenImportCsv({ ...base, creados: 1, actualizados: 3 }, "tarifa", "tarifas"))
      .toBe("1 tarifa nueva, 3 actualizadas");
  });

  it("dice '0 procesadas' cuando no hubo ningún cambio", () => {
    expect(resumenImportCsv(base, "tarifa", "tarifas")).toBe("0 tarifas procesadas");
  });

  it("agrega las descartadas con referencia a los logs", () => {
    expect(resumenImportCsv({ ...base, sinCambios: 4, descartadas: 1 }, "tarifa", "tarifas"))
      .toBe("4 sin cambios — 1 descartada (ver logs)");
    expect(resumenImportCsv({ ...base, descartadas: 3 }, "tarifa", "tarifas"))
      .toBe("0 tarifas procesadas — 3 descartadas (ver logs)");
  });
});
