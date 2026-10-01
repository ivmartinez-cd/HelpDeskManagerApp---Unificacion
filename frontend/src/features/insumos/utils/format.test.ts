import { afterEach, describe, expect, it, vi } from "vitest";
import {
  EMPTY_VALUE, formatArgDate, formatArgDateTime, formatArgTime, formatDayLabel, formatNumber, formatPercent,
  formatPlainDate, toArgDateKey, todayInArg,
} from "./format";

afterEach(() => {
  vi.useRealTimers();
});

describe("fechas de Insumos en hora argentina", () => {
  it("muestra un instante UTC en fecha y hora de Argentina", () => {
    // Intl separa fecha y hora con ", " en es-AR.
    expect(formatArgDateTime("2026-08-11T14:30:00Z")).toMatch(/^11\/08\/2026,? 11:30$/);
    expect(formatArgDate("2026-08-11T14:30:00Z")).toBe("11/08/2026");
    expect(formatArgTime("2026-08-11T14:30:00Z")).toBe("11:30");
  });

  it("un instante de madrugada UTC cae el día anterior en Argentina", () => {
    expect(formatArgDate("2026-08-11T02:00:00Z")).toBe("10/08/2026");
    expect(toArgDateKey(new Date("2026-08-11T02:00:00Z"))).toBe("2026-08-10");
  });

  it("los días calendario del backend no se corren al día anterior", () => {
    expect(formatPlainDate("2026-08-01")).toBe("01/08/2026");
    expect(formatDayLabel("2026-08-01")).toMatch(/^01[\s-]ago$/);
  });

  it("hoy es el día argentino aunque en UTC ya sea mañana", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-08-12T01:00:00Z"));
    expect(todayInArg()).toBe("2026-08-11");
  });

  it("devuelve '—' para fechas vacías o no parseables", () => {
    for (const fn of [formatArgDateTime, formatArgDate, formatArgTime, formatDayLabel, formatPlainDate]) {
      expect(fn(null)).toBe(EMPTY_VALUE);
      expect(fn(undefined)).toBe(EMPTY_VALUE);
      expect(fn("")).toBe(EMPTY_VALUE);
      expect(fn("no-es-fecha")).toBe(EMPTY_VALUE);
    }
  });
});

describe("números de Insumos", () => {
  it("usa punto de miles y coma decimal", () => {
    expect(formatNumber(4820)).toBe("4.820");
    expect(formatNumber(1234567.5)).toBe("1.234.567,5");
    expect(formatNumber(0)).toBe("0");
  });

  it("redondea el porcentaje a los decimales pedidos", () => {
    expect(formatPercent(92.75)).toBe("92,8%");
    expect(formatPercent(50, 0)).toBe("50%");
    expect(formatPercent(7, 2)).toBe("7,00%");
  });

  it("devuelve '—' sin dato o con NaN", () => {
    expect(formatNumber(null)).toBe(EMPTY_VALUE);
    expect(formatNumber(Number.NaN)).toBe(EMPTY_VALUE);
    expect(formatPercent(undefined)).toBe(EMPTY_VALUE);
    expect(formatPercent(Number.NaN)).toBe(EMPTY_VALUE);
  });
});
