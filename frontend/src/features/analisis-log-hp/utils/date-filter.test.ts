import { afterEach, describe, expect, it, vi } from "vitest";
import type { Incident, LogEvent } from "../types/analisis-log-hp";
import {
  ANALISIS_LOG_HP_PRESETS,
  dateRangeWindow,
  filterEventsByDateRange,
  filterIncidentsByDateRange,
} from "./date-filter";

afterEach(() => {
  vi.useRealTimers();
});

function rango(key: string) {
  const preset = ANALISIS_LOG_HP_PRESETS.find((p) => p.key === key);
  if (!preset?.range) throw new Error(`sin preset ${key}`);
  return preset.range();
}

const SEPTIEMBRE = { startDate: "2026-09-01", endDate: "2026-09-30" };

describe("presets de fecha del análisis de log HP", () => {
  it("con hoy jueves 1/10: semanas de lunes a domingo completas y rolling de 7 y 30 días", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 1, 15));
    expect(rango("hoy")).toEqual({ startDate: "2026-10-01", endDate: "2026-10-01" });
    expect(rango("semana")).toEqual({ startDate: "2026-09-28", endDate: "2026-10-04" });
    expect(rango("semana-pasada")).toEqual({ startDate: "2026-09-21", endDate: "2026-09-27" });
    expect(rango("mes").startDate).toBe("2026-10-01");
    expect(rango("mes-pasado")).toEqual(SEPTIEMBRE);
    expect(rango("ultimos-7")).toEqual({ startDate: "2026-09-25", endDate: "2026-10-01" });
    expect(rango("ultimos-30")).toEqual({ startDate: "2026-09-02", endDate: "2026-10-01" });
  });

  it("el domingo pertenece a la semana que empezó el lunes anterior", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 4, 23));
    expect(rango("semana")).toEqual({ startDate: "2026-09-28", endDate: "2026-10-04" });
  });

  it("en enero, el mes anterior es diciembre del año pasado", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 0, 15, 12));
    expect(rango("mes-pasado")).toEqual({ startDate: "2025-12-01", endDate: "2025-12-31" });
  });
});

describe("ventana de fechas en horario argentino", () => {
  it("sin rango no hay ventana (todo el período)", () => {
    expect(dateRangeWindow(null)).toBeNull();
  });

  it("va de las 00:00:00.000 del primer día a las 23:59:59.999 del último", () => {
    expect(dateRangeWindow(SEPTIEMBRE)).toEqual({
      minTs: Date.parse("2026-09-01T00:00:00.000-03:00"),
      maxTs: Date.parse("2026-09-30T23:59:59.999-03:00"),
    });
  });

  it("filtra eventos incluyendo los extremos del día", () => {
    const ev = (timestamp: string) => ({ timestamp }) as LogEvent;
    const eventos = [
      ev("2026-08-31T23:59:59-03:00"),
      ev("2026-09-01T00:00:00-03:00"),
      ev("2026-09-30T23:59:59-03:00"),
      ev("2026-10-01T00:00:00-03:00"),
    ];
    expect(filterEventsByDateRange(eventos, SEPTIEMBRE)).toEqual(eventos.slice(1, 3));
    expect(filterEventsByDateRange(eventos, null)).toBe(eventos);
  });

  it("un incidente se ve si su ventana pisa el rango, aunque empiece o termine afuera", () => {
    const inc = (start_time: string, end_time: string) => ({ start_time, end_time }) as Incident;
    const cruzaInicio = inc("2026-08-30T10:00:00-03:00", "2026-09-01T00:00:00-03:00");
    const cruzaFin = inc("2026-09-30T23:00:00-03:00", "2026-10-02T00:00:00-03:00");
    const envuelve = inc("2026-08-01T00:00:00-03:00", "2026-10-31T00:00:00-03:00");
    const antes = inc("2026-08-01T00:00:00-03:00", "2026-08-31T23:59:59-03:00");
    const despues = inc("2026-10-01T00:00:00-03:00", "2026-10-02T00:00:00-03:00");
    expect(filterIncidentsByDateRange([cruzaInicio, cruzaFin, envuelve, antes, despues], SEPTIEMBRE)).toEqual([
      cruzaInicio,
      cruzaFin,
      envuelve,
    ]);
  });
});
