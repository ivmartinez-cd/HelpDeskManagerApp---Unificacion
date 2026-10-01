import { describe, expect, it } from "vitest";
import type { FranjaEditable } from "../types/grilla-variantes";
import type { Slot } from "../types/turnos";
import { completarDiasDelRango } from "./variante-completar";

function franja(key: string, diaSemana: number, horaInicio = "08:00:00", horaFin = "14:00:00"): FranjaEditable {
  return { key, casillaId: "c1", diaSemana, horaInicio, horaFin, userIds: ["u1"], requiereCobertura: false };
}

function titular(...dias: number[]): Slot[] {
  return dias.map((d) => ({
    id: `s${d}`,
    casillaId: "c1",
    horaInicio: "08:00:00",
    horaFin: "14:00:00",
    diaSemana: d,
    sortOrder: 0,
    asignaciones: [],
  }));
}

function contador() {
  let n = 0;
  return () => `nueva-${++n}`;
}

describe("completar los días del rango de una variante", () => {
  it("en un rango de una semana o más copia el día base a todos los días que cubre la titular", () => {
    const franjas = [franja("a", 0), franja("b", 0, "14:00:00", "20:00:00")];
    const r = completarDiasDelRango(franjas, "2026-10-05", "2026-10-31", titular(0, 1, 2), 0, contador());
    expect(r.agregados).toEqual([1, 2]);
    expect(r.diaOrigen).toBe(0);
    expect(r.franjas.slice(2)).toEqual([
      { ...franjas[0], key: "nueva-1", diaSemana: 1 },
      { ...franjas[1], key: "nueva-2", diaSemana: 1 },
      { ...franjas[0], key: "nueva-3", diaSemana: 2 },
      { ...franjas[1], key: "nueva-4", diaSemana: 2 },
    ]);
  });

  it("en un rango corto solo completa los días de la semana que caen en el rango", () => {
    // 2026-10-01 jueves (3) y 2026-10-02 viernes (4)
    const r = completarDiasDelRango([franja("a", 3)], "2026-10-01", "2026-10-02", titular(0, 1, 2, 3, 4), 3, contador());
    expect(r.agregados).toEqual([4]);
    expect(r.diaOrigen).toBe(3);
  });

  it("si el día base no tiene franjas o no está en el rango, copia el primer día del rango que sí tenga", () => {
    const franjas = [franja("lunes", 0), franja("jueves", 3)];
    const r = completarDiasDelRango(franjas, "2026-10-01", "2026-10-02", titular(3, 4), 0, contador());
    expect(r.diaOrigen).toBe(3);
    expect(r.franjas[2]).toEqual({ ...franjas[1], key: "nueva-1", diaSemana: 4 });
  });

  it("no toca nada sin franjas armadas, sin días faltantes o con rango inválido", () => {
    const franjas = [franja("a", 0)];
    const sinCambios = (r: ReturnType<typeof completarDiasDelRango>, f: FranjaEditable[]) => {
      expect(r).toEqual({ franjas: f, agregados: [], diaOrigen: null });
      expect(r.franjas).toBe(f);
    };
    const vacias: FranjaEditable[] = [];
    sinCambios(completarDiasDelRango(vacias, "2026-10-05", "2026-10-31", titular(0, 1), 0, contador()), vacias);
    sinCambios(completarDiasDelRango(franjas, "2026-10-05", "2026-10-31", titular(0), 0, contador()), franjas);
    // año a medio tipear en el <input type="date">
    sinCambios(completarDiasDelRango(franjas, "0020-10-05", "2026-10-31", titular(0, 1), 0, contador()), franjas);
    // hasta anterior a desde
    sinCambios(completarDiasDelRango(franjas, "2026-10-31", "2026-10-05", titular(0, 1), 0, contador()), franjas);
  });
});
