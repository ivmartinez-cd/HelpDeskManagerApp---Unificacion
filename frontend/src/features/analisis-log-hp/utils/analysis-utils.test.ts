import { afterEach, describe, expect, it, vi } from "vitest";
import type { Incident, LogEvent, Severity } from "../types/analisis-log-hp";
import {
  SEV_COLOR,
  buildFrequencyChartData,
  buildHeatmapData,
  buildVolumeChartData,
  computeErrorRate,
  filterEventsByDays,
  filterEventsBySeverity,
  filterIncidentsBySeverity,
  fmtDatetime,
  lastCriticalIncident,
  normSev,
  relativeTime,
} from "./analysis-utils";

afterEach(() => {
  vi.useRealTimers();
});

function ev(extra: Partial<LogEvent> = {}): LogEvent {
  return {
    type: "INFO",
    code: "C0",
    timestamp: "2026-09-15T10:00:00-03:00",
    counter: 0,
    firmware: null,
    help_reference: null,
    code_severity: null,
    code_description: null,
    code_solution_url: null,
    ...extra,
  };
}

function inc(code: string, severity: Severity, occurrences = 1, end_time = "2026-09-15T10:00:00-03:00"): Incident {
  return {
    id: `${code}-${end_time}`,
    code,
    classification: "",
    severity,
    severity_weight: 0,
    occurrences,
    start_time: end_time,
    end_time,
    counter_range: [0, 0],
    sds_link: null,
  };
}

describe("severidad de eventos del log HP", () => {
  it("cualquier valor que no sea ERROR/WARNING/INFO es UNKNOWN", () => {
    expect(normSev("ERROR")).toBe("ERROR");
    expect(normSev("error")).toBe("UNKNOWN");
    expect(normSev(null)).toBe("UNKNOWN");
    expect(normSev(undefined)).toBe("UNKNOWN");
  });
});

describe("tiempos relativos y fechas", () => {
  it("dice hace un momento, minutos, horas o días según la antigüedad", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-01T12:00:00Z"));
    expect(relativeTime("2026-10-01T11:59:30Z")).toBe("hace un momento");
    expect(relativeTime("2026-10-01T11:15:00Z")).toBe("hace 45 min");
    expect(relativeTime("2026-10-01T09:00:00Z")).toBe("hace 3 h");
    expect(relativeTime("2026-09-28T11:00:00Z")).toBe("hace 3 d");
  });

  it("formatea fecha y hora en horario argentino", () => {
    expect(fmtDatetime("2026-09-15T13:05:00Z")).toBe("15/09/26, 10:05 a. m.");
  });
});

describe("KPI de último error crítico", () => {
  it("devuelve el ERROR que terminó más tarde, ignorando warnings más nuevos", () => {
    const viejo = inc("E1", "ERROR", 1, "2026-09-10T10:00:00Z");
    const nuevo = inc("E2", "ERROR", 1, "2026-09-12T10:00:00Z");
    const warning = inc("W1", "WARNING", 1, "2026-09-20T10:00:00Z");
    expect(lastCriticalIncident([viejo, warning, nuevo])).toBe(nuevo);
  });

  it("sin errores no hay KPI", () => {
    expect(lastCriticalIncident([inc("W1", "WARNING")])).toBeNull();
  });
});

describe("KPI de tasa de errores (páginas por error)", () => {
  it("sin al menos dos contadores positivos no hay dato", () => {
    expect(computeErrorRate([ev({ counter: 100 }), ev({ counter: 0 })])).toEqual({
      label: "—",
      sub: "sin datos de contador",
      pagesInPeriod: 0,
      totalCounter: 0,
    });
  });

  it("si el contador no avanzó no hay rango", () => {
    expect(computeErrorRate([ev({ counter: 500 }), ev({ counter: 500 })])).toMatchObject({
      label: "—",
      sub: "sin rango de contador",
      totalCounter: 500,
    });
  });

  it("sin eventos ERROR informa sin errores", () => {
    expect(computeErrorRate([ev({ counter: 100 }), ev({ counter: 300 })])).toMatchObject({
      label: "Sin errores",
      sub: "sin errores críticos",
      pagesInPeriod: 200,
      totalCounter: 300,
    });
  });

  it("divide las páginas del período por los eventos ERROR y muestra el código más frecuente", () => {
    const eventos = [
      ev({ counter: 1000, type: "ERROR", code: "E1" }),
      ev({ counter: 3000, type: "ERROR", code: "E2" }),
      ev({ counter: 5000, type: "ERROR", code: "E1" }),
      ev({ counter: 4000, type: "WARNING", code: "W1" }),
    ];
    // 4000 páginas / 3 errores = 1333
    expect(computeErrorRate(eventos)).toEqual({
      label: "1 c/1.333 pág.",
      sub: "E1",
      pagesInPeriod: 4000,
      totalCounter: 5000,
    });
  });

  it("con más errores que páginas muestra la cantidad de errores", () => {
    const eventos = [
      ev({ counter: 100, type: "ERROR", code: "E1" }),
      ev({ counter: 101, type: "ERROR", code: "E1" }),
      ev({ counter: 101, type: "ERROR", code: "E1" }),
    ];
    expect(computeErrorRate(eventos).label).toBe("3 err.");
  });
});

describe("gráficos del análisis", () => {
  it("el heatmap cuenta por día de semana y franja de 3 h en horario local", () => {
    const { matrix, maxValue } = buildHeatmapData([
      ev({ timestamp: "2026-09-14T10:30:00-03:00" }), // lunes, 9-12
      ev({ timestamp: "2026-09-14T11:59:00-03:00" }),
      ev({ timestamp: "2026-09-13T23:59:00-03:00" }), // domingo, 21-24
    ]);
    expect(matrix[1][3]).toBe(2);
    expect(matrix[0][7]).toBe(1);
    expect(maxValue).toBe(2);
  });

  it("el heatmap vacío tiene máximo 1 para no dividir por cero", () => {
    expect(buildHeatmapData([]).maxValue).toBe(1);
  });

  it("el volumen por día ordena las fechas y cuenta sin severidad como info", () => {
    expect(
      buildVolumeChartData([
        ev({ timestamp: "2026-09-15T10:00:00", code_severity: "ERROR" }),
        ev({ timestamp: "2026-09-14T10:00:00", code_severity: "WARNING" }),
        ev({ timestamp: "2026-09-15T11:00:00", code_severity: null }),
        ev({ timestamp: "2026-09-15T12:00:00", code_severity: "ERROR" }),
      ]),
    ).toEqual({ labels: ["14/09", "15/09"], errors: [0, 2], warnings: [1, 0], infos: [0, 1] });
  });

  it("frecuencia: suma ocurrencias por código y lo pinta con su severidad más grave", () => {
    expect(
      buildFrequencyChartData([inc("A", "WARNING", 3), inc("B", "INFO", 10), inc("A", "ERROR", 2)]),
    ).toEqual({ labels: ["B", "A"], counts: [10, 5], colors: [SEV_COLOR.INFO, SEV_COLOR.ERROR] });
  });

  it("frecuencia: muestra solo los 8 códigos más frecuentes", () => {
    const incidentes = Array.from({ length: 9 }, (_, i) => inc(`C${i}`, "INFO", i + 1));
    const { labels } = buildFrequencyChartData(incidentes);
    expect(labels).toHaveLength(8);
    expect(labels).not.toContain("C0");
  });
});

describe("filtros del análisis", () => {
  it("filtra por los últimos N días; 0 son todos", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-01T12:00:00Z"));
    const dentro = ev({ timestamp: "2026-09-24T12:00:00Z" });
    const fuera = ev({ timestamp: "2026-09-24T11:59:59Z" });
    expect(filterEventsByDays([dentro, fuera], 7)).toEqual([dentro]);
    expect(filterEventsByDays([dentro, fuera], 0)).toEqual([dentro, fuera]);
  });

  it("filtra por severidades activas; sin ninguna activa no filtra", () => {
    const error = ev({ code_severity: "ERROR" });
    const sinSev = ev({ code_severity: null });
    expect(filterEventsBySeverity([error, sinSev], new Set<Severity>(["UNKNOWN"]))).toEqual([sinSev]);
    expect(filterEventsBySeverity([error, sinSev], new Set())).toEqual([error, sinSev]);

    const w = inc("W", "WARNING");
    const e = inc("E", "ERROR");
    expect(filterIncidentsBySeverity([w, e], new Set<Severity>(["ERROR"]))).toEqual([e]);
    expect(filterIncidentsBySeverity([w, e], new Set())).toEqual([w, e]);
  });
});
