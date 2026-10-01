import { describe, expect, it } from "vitest";
import { nombreCompleto, ordenarPorNombre } from "./empleados";

describe("nombres de empleados en combos", () => {
  it("muestra nombre y apellido", () => {
    expect(nombreCompleto({ firstName: "Ana", lastName: "Pérez" })).toBe("Ana Pérez");
  });

  it("ordena por nombre completo con reglas del castellano y sin mutar la lista original", () => {
    const original = [
      { firstName: "Zoe", lastName: "Alvarez" },
      { firstName: "Ñandú", lastName: "Gómez" },
      { firstName: "Ángel", lastName: "Zapata" },
      { firstName: "alberto", lastName: "Ruiz" },
    ];
    const ordenados = ordenarPorNombre(original);
    expect(ordenados.map(nombreCompleto)).toEqual(["alberto Ruiz", "Ángel Zapata", "Ñandú Gómez", "Zoe Alvarez"]);
    expect(original[0].firstName).toBe("Zoe");
  });
});
