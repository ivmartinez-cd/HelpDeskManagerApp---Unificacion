import { afterEach, describe, expect, it, vi } from "vitest";
import {
  accentText,
  agingDotColor,
  fechaLarga,
  fmtInt,
  fmtPct,
  heatCellStyle,
  minutosDesde,
  periodoLabel,
  periodoOffset,
  textoHace,
  tint,
} from "./formato-dashboard";

afterEach(() => {
  vi.useRealTimers();
});

const AHORA = Date.parse("2026-10-01T12:00:00Z");
const hace = (min: number) => new Date(AHORA - min * 60_000).toISOString();

describe("formatos numéricos del dashboard", () => {
  it("usa punto de miles y coma decimal, con hasta 2 decimales en porcentajes", () => {
    expect(fmtInt(12345)).toBe("12.345");
    expect(fmtPct(1234.567)).toBe("1.234,57");
    expect(fmtPct(50)).toBe("50");
  });
});

describe("tintes por color de operador", () => {
  it("solo mezcla el color si es hex de 6 dígitos; si no, cae a un tinte neutro", () => {
    expect(tint("#F7941D")).toBe("color-mix(in srgb, #F7941D var(--tint-alpha, 13%), transparent)");
    expect(tint("#fff")).toBe("color-mix(in srgb, var(--foreground) 6%, transparent)");
    expect(tint("red")).toBe("color-mix(in srgb, var(--foreground) 6%, transparent)");
  });

  it("oscurece el texto de acento solo para hex; otro formato pasa tal cual", () => {
    expect(accentText("#22c55e")).toBe("color-mix(in oklch, #22c55e var(--accent-text-weight, 100%), black)");
    expect(accentText("rgb(1,2,3)")).toBe("rgb(1,2,3)");
  });
});

describe("intensidad del heatmap semanal", () => {
  it("0 vacía, 1-2 tenue, 3-4 media, 5 o más naranja sólido", () => {
    expect(heatCellStyle(0)).toEqual({ bg: "var(--chart-empty)", text: "transparent" });
    expect(heatCellStyle(2).bg).toBe("rgba(247,148,29,.14)");
    expect(heatCellStyle(3).bg).toBe("rgba(247,148,29,.38)");
    expect(heatCellStyle(4).bg).toBe("rgba(247,148,29,.38)");
    expect(heatCellStyle(5)).toEqual({ bg: "#F7941D", text: "#fff" });
  });
});

describe("semáforo de antigüedad de pendientes", () => {
  it("verde por debajo de 5 días, ámbar desde 5 y rojo desde 10", () => {
    expect(agingDotColor(4)).toBe("#22c55e");
    expect(agingDotColor(5)).toBe("#d69e08");
    expect(agingDotColor(9)).toBe("#d69e08");
    expect(agingDotColor(10)).toBe("#ef4444");
  });
});

describe("frescura del dato", () => {
  it("minutosDesde devuelve null sin fecha o con fecha inválida y nunca negativo", () => {
    expect(minutosDesde(null, AHORA)).toBeNull();
    expect(minutosDesde("no-es-fecha", AHORA)).toBeNull();
    expect(minutosDesde(hace(-5), AHORA)).toBe(0);
    expect(minutosDesde(hace(12), AHORA)).toBe(12);
  });

  it("textoHace: momento, minutos, horas redondeadas y días desde las 48 h", () => {
    expect(textoHace(undefined, AHORA)).toBe("sin fecha");
    expect(textoHace(hace(1), AHORA)).toBe("hace un momento");
    expect(textoHace(hace(2), AHORA)).toBe("hace 2 min");
    expect(textoHace(hace(59), AHORA)).toBe("hace 59 min");
    expect(textoHace(hace(90), AHORA)).toBe("hace 2 h");
    expect(textoHace(hace(47 * 60), AHORA)).toBe("hace 47 h");
    expect(textoHace(hace(72 * 60), AHORA)).toBe("hace 3 d");
  });
});

describe("fechas y períodos del encabezado y la tendencia SLA", () => {
  it("fechaLarga pone en mayúscula el día de la semana", () => {
    expect(fechaLarga(new Date(2026, 7, 22))).toBe("Sábado, 22 de agosto");
  });

  it("periodoOffset da AAAAMM del mes actual desplazado, cruzando el año", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 0, 31, 12));
    expect(periodoOffset(0)).toBe("202601");
    expect(periodoOffset(-1)).toBe("202512");
    expect(periodoOffset(-12)).toBe("202501");
  });

  it("periodoLabel da el mes abreviado capitalizado y sin punto", () => {
    expect(periodoLabel("202603")).toBe("Mar");
    expect(periodoLabel("202609")).toBe("Sept");
  });
});
