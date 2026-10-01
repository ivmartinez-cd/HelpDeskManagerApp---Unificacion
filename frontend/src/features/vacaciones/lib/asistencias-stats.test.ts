import { describe, expect, it } from "vitest";
import type { Ausencia, Solicitud, TipoAusencia } from "../types/vacaciones";
import { diasDelMes, estadoCelda, fechaIso, statsDelAnio } from "./asistencias-stats";
import { COLOR_VACACIONES, TIPO_AUSENCIA } from "./tipos-ausencia";

function ausencia(
  tipo: TipoAusencia,
  startDate: string,
  endDate: string,
  extra: Partial<Ausencia> = {},
): Ausencia {
  return {
    id: `${tipo}-${startDate}`,
    empleadoId: "e1",
    empleadoNombre: "Ana Pérez",
    empleadoColor: "#000",
    sectorNombre: "Soporte",
    sectorColor: "#000",
    startDate,
    endDate,
    daysCount: 1,
    halfDay: false,
    tipo,
    reason: null,
    status: "APPROVED",
    createdAt: "2026-01-01T00:00:00Z",
    horaDesde: null,
    horaHasta: null,
    certificadoUrl: null,
    ...extra,
  };
}

function vacacion(startDate: string, endDate: string, extra: Partial<Solicitud> = {}): Solicitud {
  return {
    id: `vac-${startDate}`,
    empleadoId: "e1",
    empleadoNombre: "Ana Pérez",
    empleadoColor: "#000",
    sectorNombre: "Soporte",
    sectorColor: "#000",
    startDate,
    endDate,
    daysRequested: 1,
    chargedToYear: 2026,
    reason: null,
    status: "APPROVED",
    createdAt: "2026-01-01T00:00:00Z",
    aprobaciones: [],
    ...extra,
  };
}

describe("helpers de fecha de la grilla anual", () => {
  it("arma la fecha ISO con ceros a la izquierda", () => {
    expect(fechaIso(2026, 3, 5)).toBe("2026-03-05");
  });

  it("cuenta los días del mes, incluido febrero bisiesto", () => {
    expect(diasDelMes(2026, 2)).toBe(28);
    expect(diasDelMes(2028, 2)).toBe(29);
    expect(diasDelMes(2026, 12)).toBe(31);
  });
});

describe("estado de una celda de asistencias", () => {
  const feriados = new Set(["2026-05-25"]);

  it("el feriado tiene prioridad sobre vacaciones y bajas", () => {
    const celda = estadoCelda(
      "2026-05-25",
      [ausencia("BAJA_ENFERMEDAD", "2026-05-25", "2026-05-25")],
      [vacacion("2026-05-20", "2026-05-30")],
      feriados,
    );
    expect(celda).toEqual({ color: "#8b5cf6", label: "Feriado", halfDay: false, esFeriado: true });
  });

  it("las vacaciones aprobadas tapan una baja del mismo día", () => {
    const celda = estadoCelda(
      "2026-05-21",
      [ausencia("BAJA_ENFERMEDAD", "2026-05-21", "2026-05-21")],
      [vacacion("2026-05-20", "2026-05-22")],
      feriados,
    );
    expect(celda).toEqual({ color: COLOR_VACACIONES, label: "Vacaciones", halfDay: false, esFeriado: false });
  });

  it("ignora vacaciones y bajas que no están aprobadas", () => {
    const celda = estadoCelda(
      "2026-05-21",
      [ausencia("BAJA_ENFERMEDAD", "2026-05-21", "2026-05-21", { status: "PENDING" })],
      [vacacion("2026-05-20", "2026-05-22", { status: "REJECTED" })],
      feriados,
    );
    expect(celda).toBeNull();
  });

  it("muestra el tipo de baja con su motivo y si es medio día", () => {
    const celda = estadoCelda(
      "2026-06-10",
      [ausencia("TRAMITE_PERSONAL", "2026-06-10T00:00:00", "2026-06-10T00:00:00", { reason: "DNI", halfDay: true })],
      [],
      feriados,
    );
    expect(celda).toEqual({
      color: TIPO_AUSENCIA.TRAMITE_PERSONAL.color,
      label: "Trámites personales — DNI",
      halfDay: true,
      esFeriado: false,
    });
  });

  it("incluye los días de inicio y fin del rango", () => {
    const aus = [ausencia("GUARDIA", "2026-06-10", "2026-06-12")];
    expect(estadoCelda("2026-06-10", aus, [], feriados)?.label).toBe("Guardia");
    expect(estadoCelda("2026-06-12", aus, [], feriados)?.label).toBe("Guardia");
    expect(estadoCelda("2026-06-13", aus, [], feriados)).toBeNull();
  });
});

describe("estadísticas anuales de asistencia", () => {
  // 2026 empieza jueves: 52 semanas + 1 jueves = 261 días hábiles sin feriados.
  const feriados = new Set(["2026-05-25", "2026-08-01"]); // lunes y sábado

  it("sin novedades, los días trabajados son los hábiles menos los feriados en día de semana", () => {
    const stats = statsDelAnio(2026, [], [], feriados);
    expect(stats.totalBajas).toBe(0);
    expect(stats.diasTrabajados).toBe(260);
  });

  it("suma vacaciones, bajas y medios días según las reglas del legacy", () => {
    const vacaciones = [
      vacacion("2026-01-05", "2026-01-11"), // lunes a domingo: 7 corridos, 5 hábiles
      vacacion("2026-07-06", "2026-07-10", { status: "PENDING" }),
    ];
    const ausencias = [
      ausencia("BAJA_ENFERMEDAD", "2026-01-06", "2026-01-06"), // cae en vacaciones: no cuenta
      ausencia("BAJA_ENFERMEDAD", "2026-02-02", "2026-02-03"),
      ausencia("DESCUENTO_DIA", "2026-03-02", "2026-03-02", { halfDay: true }),
      ausencia("HOME_OFFICE", "2026-03-03", "2026-03-03"),
      ausencia("TRAMITE_PERSONAL", "2026-03-04", "2026-03-04", { halfDay: true }),
      ausencia("DIA_ESTUDIO", "2026-03-05", "2026-03-05", { status: "REJECTED" }),
    ];
    const stats = statsDelAnio(2026, ausencias, vacaciones, feriados);

    expect(stats.vacaciones).toBe(7);
    expect(stats.enfermedad).toBe(2);
    // home office no es baja; los medios días suman 0,5
    expect(stats.totalBajas).toBe(7 + 2 + 0.5 + 0.5);
    expect(stats.diasTrabajados).toBe(260 - (5 + 2 + 0.5 + 0.5));
    // descuento cuenta medios días; el resto de los tipos cuenta días con novedad
    expect(stats.descuento).toBe(0.5);
    expect(stats.tramitesEstudio).toBe(1);
    expect(stats.porTipo.HOME_OFFICE).toBe(1);
    expect(stats.porTipo.DIA_ESTUDIO).toBe(0);
  });

  it("los días de baja en fin de semana suman al total pero no restan días trabajados", () => {
    const stats = statsDelAnio(2026, [ausencia("BAJA_ENFERMEDAD", "2026-02-06", "2026-02-09")], [], new Set());
    // viernes a lunes: 4 corridos, 2 hábiles
    expect(stats.totalBajas).toBe(4);
    expect(stats.enfermedad).toBe(4);
    expect(stats.diasTrabajados).toBe(261 - 2);
  });
});
