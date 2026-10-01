import { describe, expect, it } from "vitest";
import type { FranjaEditable } from "../types/grilla-variantes";
import type { Slot } from "../types/turnos";
import {
  advertenciasDeOperadores,
  diaSemanaDeIso,
  diasActivosDeRango,
  erroresDeFranjas,
  huecosDeCobertura,
} from "./variante-validacion";

let n = 0;
function franja(over: Partial<FranjaEditable>): FranjaEditable {
  n += 1;
  return {
    key: `f${n}`,
    casillaId: "mesa",
    diaSemana: 0,
    horaInicio: "08:00",
    horaFin: "12:00",
    userIds: ["ana"],
    requiereCobertura: false,
    ...over,
  };
}

function slot(over: Partial<Slot>): Slot {
  return {
    id: "s",
    casillaId: "mesa",
    horaInicio: "08:00",
    horaFin: "17:00",
    diaSemana: 0,
    sortOrder: 0,
    asignaciones: [],
    ...over,
  };
}

const nombre = (id: string) => id.toUpperCase();

describe("erroresDeFranjas", () => {
  it("bloquea inicio >= fin y franjas incompletas", () => {
    const errores = erroresDeFranjas(
      [franja({ horaInicio: "12:00", horaFin: "08:00" }), franja({ horaFin: "" })],
      nombre,
    );
    expect(errores.map((e) => e.mensaje)).toEqual([
      "MESA 12:00–08:00: el inicio debe ser menor que el fin.",
      "MESA: completá inicio y fin.",
    ]);
  });

  it("bloquea solapes en la misma casilla y día, no entre días distintos", () => {
    const a = franja({ horaInicio: "08:00", horaFin: "12:00" });
    const b = franja({ horaInicio: "11:00", horaFin: "14:00" });
    const otroDia = franja({ diaSemana: 1, horaInicio: "09:00", horaFin: "10:00" });
    const errores = erroresDeFranjas([a, b, otroDia], nombre);
    expect(errores).toHaveLength(1);
    expect(errores[0].keys).toEqual([a.key, b.key]);
  });

  it("franjas que se tocan sin pisarse son válidas", () => {
    const errores = erroresDeFranjas(
      [franja({ horaFin: "12:00" }), franja({ horaInicio: "12:00", horaFin: "16:00" })],
      nombre,
    );
    expect(errores).toEqual([]);
  });
});

describe("advertenciasDeOperadores", () => {
  it("avisa (sin bloquear) si un operador está en dos franjas que se pisan el mismo día", () => {
    const a = franja({ casillaId: "mesa" });
    const b = franja({ casillaId: "calle", horaInicio: "10:00", horaFin: "13:00" });
    const advertencias = advertenciasDeOperadores([a, b], nombre, nombre);
    expect(advertencias).toHaveLength(1);
    expect(advertencias[0].mensaje).toContain("ANA está en MESA");
  });
});

describe("huecosDeCobertura", () => {
  it("devuelve lo que la titular cubre y la variante no", () => {
    const huecos = huecosDeCobertura(
      [franja({ horaInicio: "08:00", horaFin: "12:00" }), franja({ horaInicio: "13:00", horaFin: "15:00" })],
      [slot({})],
    );
    expect(huecos.map((h) => `${h.horaInicio}-${h.horaFin}`)).toEqual(["12:00-13:00", "15:00-17:00"]);
  });

  it("ignora los días fuera del rango activo", () => {
    expect(huecosDeCobertura([], [slot({ diaSemana: 3 })], new Set([0]))).toEqual([]);
  });
});

describe("días de la semana", () => {
  it("numera de lunes (0) a domingo (6) en fecha local", () => {
    expect(diaSemanaDeIso("2026-09-14")).toBe(0); // lunes
    expect(diaSemanaDeIso("2026-09-20")).toBe(6); // domingo
  });

  it("un rango corto activa solo sus días; una semana o más, todos", () => {
    expect([...(diasActivosDeRango("2026-09-18", "2026-09-20") ?? [])].sort()).toEqual([4, 5, 6]);
    expect(diasActivosDeRango("2026-09-14", "2026-09-20")).toBeUndefined();
  });
});
