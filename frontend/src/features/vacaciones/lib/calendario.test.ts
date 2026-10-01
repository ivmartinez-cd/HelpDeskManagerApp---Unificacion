import { describe, expect, it } from "vitest";
import type { EventoCalendario } from "../types/vacaciones";
import {
  buildGridDays,
  eventosDelDia,
  feriadoDelDia,
  finInclusivo,
  labelMes,
  rangoDeGrilla,
  rangoSemanaProxima,
} from "./calendario";

function evento(tipo: EventoCalendario["tipo"], start: string, end: string, id = start): EventoCalendario {
  return {
    id,
    title: id,
    start,
    end,
    tipo,
    color: "#000",
    borderColor: null,
    status: null,
    empleado: null,
    sector: null,
    dias: null,
    restantes: null,
    reason: null,
  };
}

describe("grilla mensual de lunes a domingo", () => {
  it("arranca el lunes anterior al día 1 y recorta la sexta fila si es toda del mes siguiente", () => {
    // octubre 2026 empieza jueves
    const celdas = buildGridDays(2026, 10, "2026-10-01");
    expect(celdas).toHaveLength(35);
    expect(celdas[0]).toEqual({ iso: "2026-09-28", day: 28, inMonth: false, isToday: false, isWeekend: false });
    expect(celdas[3]).toEqual({ iso: "2026-10-01", day: 1, inMonth: true, isToday: true, isWeekend: false });
    expect(celdas[5].isWeekend).toBe(true);
    expect(celdas[6].isWeekend).toBe(true);
    expect(celdas[34]).toMatchObject({ iso: "2026-11-01", inMonth: false });
    expect(celdas.filter((c) => c.isToday)).toHaveLength(1);
  });

  it("usa seis filas cuando el mes no entra en cinco", () => {
    // marzo 2026 empieza domingo y tiene 31 días
    const celdas = buildGridDays(2026, 3, "");
    expect(celdas).toHaveLength(42);
    expect(celdas[6].iso).toBe("2026-03-01");
    expect(celdas[36].iso).toBe("2026-03-31");
    expect(celdas[41].iso).toBe("2026-04-05");
  });

  it("el rango a pedir es el de la grilla visible, no el del mes", () => {
    expect(rangoDeGrilla(2026, 10)).toEqual({ desde: "2026-09-28", hasta: "2026-11-01" });
    expect(rangoDeGrilla(2026, 3)).toEqual({ desde: "2026-02-23", hasta: "2026-04-05" });
  });

  it("nombra el mes en castellano", () => {
    expect(labelMes(2026, 1)).toBe("enero de 2026");
    expect(labelMes(2026, 12)).toBe("diciembre de 2026");
  });
});

describe("eventos de un día", () => {
  const eventos = [
    evento("vacation", "2026-10-05", "2026-10-10", "vac"),
    evento("holiday", "2026-10-12", "2026-10-13", "feriado"),
  ];

  it("una vacación cubre desde start inclusive hasta end exclusivo", () => {
    expect(eventosDelDia(eventos, "2026-10-04")).toEqual([]);
    expect(eventosDelDia(eventos, "2026-10-05").map((e) => e.id)).toEqual(["vac"]);
    expect(eventosDelDia(eventos, "2026-10-09").map((e) => e.id)).toEqual(["vac"]);
    expect(eventosDelDia(eventos, "2026-10-10")).toEqual([]);
  });

  it("los feriados no cuentan como vacaciones y se buscan por su día de inicio", () => {
    expect(eventosDelDia(eventos, "2026-10-12")).toEqual([]);
    expect(feriadoDelDia(eventos, "2026-10-12")?.id).toBe("feriado");
    expect(feriadoDelDia(eventos, "2026-10-05")).toBeUndefined();
  });

  it("el último día inclusive es el anterior al end exclusivo, cruzando meses", () => {
    expect(finInclusivo(evento("vacation", "2026-02-20", "2026-03-01"))).toBe("2026-02-28");
    expect(finInclusivo(evento("vacation", "2026-12-28", "2027-01-01"))).toBe("2026-12-31");
  });
});

describe("semana próxima", () => {
  it("va del lunes al domingo siguientes, sea cual sea el día de hoy", () => {
    expect(rangoSemanaProxima("2026-10-01")).toEqual({ desde: "2026-10-05", hasta: "2026-10-11" }); // jueves
    expect(rangoSemanaProxima("2026-10-04")).toEqual({ desde: "2026-10-05", hasta: "2026-10-11" }); // domingo
    expect(rangoSemanaProxima("2026-10-05")).toEqual({ desde: "2026-10-12", hasta: "2026-10-18" }); // lunes
  });

  it("cruza el fin de año", () => {
    expect(rangoSemanaProxima("2026-12-30")).toEqual({ desde: "2027-01-04", hasta: "2027-01-10" });
  });
});
