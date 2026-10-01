import { describe, expect, it } from "vitest";
import type { ResolvedShift } from "@/features/turnos/types/turnos";
import { enHorarioSt, esOperadorStEnTurno, franjasStVigentes } from "./turno-st";

function shift(casillaNombre: string, horaInicio: string, horaFin: string, userIds: string[] = []): ResolvedShift {
  return {
    slotId: `${casillaNombre}-${horaInicio}`,
    casillaId: casillaNombre,
    casillaNombre,
    horaInicio,
    horaFin,
    diaSemana: 3,
    operadores: userIds.map((userId) => ({ userId, userName: userId })),
    isCurrent: false,
    isNext: false,
  };
}

// Hora local de Argentina (el config fija TZ=America/Argentina/Buenos_Aires).
const a = (hhmm: string) => new Date(`2026-10-01T${hhmm}:00-03:00`);

describe("franja de Servicio Técnico en curso", () => {
  const shifts = [
    shift("ST", "08:00:00", "14:00:00", ["u1"]),
    shift(" st ", "14:00:00", "20:00:00", ["u2"]),
    shift("Mesa", "08:00:00", "20:00:00", ["u3"]),
  ];

  it("solo cuenta la casilla ST, sin importar mayúsculas ni espacios", () => {
    expect(franjasStVigentes(shifts, a("15:00")).map((s) => s.slotId)).toEqual([" st -14:00:00"]);
  });

  it("el inicio es inclusivo y el fin exclusivo", () => {
    expect(franjasStVigentes(shifts, a("08:00")).map((s) => s.slotId)).toEqual(["ST-08:00:00"]);
    expect(franjasStVigentes(shifts, a("14:00")).map((s) => s.slotId)).toEqual([" st -14:00:00"]);
    expect(enHorarioSt(shifts, a("20:00"))).toBe(false);
    expect(enHorarioSt(shifts, a("07:59"))).toBe(false);
  });

  it("usa la hora del momento, no la marca isCurrent del fetch", () => {
    const marcadas = shifts.map((s) => ({ ...s, isCurrent: true }));
    expect(enHorarioSt(marcadas, a("21:00"))).toBe(false);
  });

  it("el usuario está de turno ST solo si figura como operador de la franja vigente", () => {
    expect(esOperadorStEnTurno(shifts, "u1", a("09:30"))).toBe(true);
    expect(esOperadorStEnTurno(shifts, "u2", a("09:30"))).toBe(false);
    expect(esOperadorStEnTurno(shifts, "u3", a("09:30"))).toBe(false); // está en Mesa, no en ST
  });
});
