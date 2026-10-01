import { afterEach, describe, expect, it, vi } from "vitest";
import { formatPlainDate, toArgDateKey, todayInArg } from "./date-arg";

afterEach(() => {
  vi.useRealTimers();
});

describe("fechas calendario en huso Argentina", () => {
  it("a las 01:00 UTC todavía es el día anterior en Argentina", () => {
    expect(toArgDateKey(new Date("2026-10-01T01:00:00Z"))).toBe("2026-09-30");
    expect(toArgDateKey(new Date("2026-10-01T03:00:00Z"))).toBe("2026-10-01");
  });

  it("hoy se calcula en Argentina, no en UTC", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-02T02:30:00Z"));
    expect(todayInArg()).toBe("2026-10-01");
  });

  it("muestra AAAA-MM-DD como DD/MM/AAAA sin pasar por Date", () => {
    expect(formatPlainDate("2026-08-11")).toBe("11/08/2026");
  });

  it("muestra un guion si la fecha falta o está incompleta", () => {
    expect(formatPlainDate(null)).toBe("—");
    expect(formatPlainDate(undefined)).toBe("—");
    expect(formatPlainDate("")).toBe("—");
    expect(formatPlainDate("2026-08")).toBe("—");
  });
});
