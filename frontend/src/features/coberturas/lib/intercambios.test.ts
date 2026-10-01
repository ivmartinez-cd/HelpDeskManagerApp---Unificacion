import { afterEach, describe, expect, it, vi } from "vitest";
import type { Cobertura, FilaCoberturas } from "../types/coberturas";
import {
  agruparFilas,
  estadoFila,
  filaCoincide,
  filaKey,
  intercambioAPayload,
  nombreOperadorA,
  nombreOperadorB,
} from "./intercambios";

afterEach(() => {
  vi.useRealTimers();
});

function cob(id: string, extra: Partial<Cobertura> = {}): Cobertura {
  return {
    id,
    ausenteId: `aus-${id}`,
    ausenteNombre: `Ausente ${id}`,
    reemplazanteId: `rem-${id}`,
    reemplazanteNombre: `Reemplazo ${id}`,
    desde: "2026-10-05",
    hasta: "2026-10-09",
    alcanceTotal: true,
    alcanceItems: [],
    estado: "ACTIVA",
    motivo: null,
    intercambioId: null,
    ...extra,
  };
}

describe("agrupado de intercambios en la tabla de coberturas", () => {
  it("junta las dos mitades de un intercambio en una fila, en la posición de la primera", () => {
    const ida = cob("ida", { intercambioId: "i1" });
    const vuelta = cob("vuelta", { intercambioId: "i1" });
    const filas = agruparFilas([cob("a"), ida, cob("b"), vuelta]);
    expect(filas).toEqual([
      { tipo: "cobertura", cobertura: cob("a") },
      { tipo: "intercambio", intercambio: { id: "i1", ida, vuelta } },
      { tipo: "cobertura", cobertura: cob("b") },
    ]);
  });

  it("muestra como coberturas sueltas un intercambio que no tiene exactamente dos mitades", () => {
    const huerfana = cob("h", { intercambioId: "i1" });
    const triple = ["x", "y", "z"].map((id) => cob(id, { intercambioId: "i2" }));
    const filas = agruparFilas([huerfana, ...triple]);
    expect(filas.map((f) => f.tipo)).toEqual(["cobertura", "cobertura", "cobertura", "cobertura"]);
  });

  it("la clave de fila distingue coberturas de intercambios", () => {
    const [comun, par] = agruparFilas([
      cob("a"),
      cob("ida", { intercambioId: "i1" }),
      cob("vuelta", { intercambioId: "i1" }),
    ]);
    expect(filaKey(comun)).toBe("a");
    expect(filaKey(par)).toBe("intercambio:i1");
  });
});

describe("estado y búsqueda de una fila", () => {
  const par: FilaCoberturas = {
    tipo: "intercambio",
    intercambio: {
      id: "i1",
      ida: cob("ida", { desde: "2026-10-05", hasta: "2026-10-09" }),
      vuelta: cob("vuelta", { ausenteNombre: null, ausenteId: "beto-id", desde: "2026-01-01", hasta: "2026-01-02" }),
    },
  };

  it("el estado de un intercambio sale de la ida", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-06T15:00:00Z"));
    expect(estadoFila(par)).toBe("activa");
    expect(estadoFila({ tipo: "cobertura", cobertura: cob("a", { estado: "CANCELADA" }) })).toBe("cancelada");
  });

  it("busca en ausente y reemplazante de una cobertura, sin distinguir mayúsculas del dato", () => {
    const fila: FilaCoberturas = { tipo: "cobertura", cobertura: cob("a", { ausenteNombre: "Ana PÉREZ" }) };
    expect(filaCoincide(fila, "pérez")).toBe(true);
    expect(filaCoincide(fila, "reemplazo a")).toBe(true);
    expect(filaCoincide(fila, "rem-a")).toBe(true);
    expect(filaCoincide(fila, "zzz")).toBe(false);
  });

  it("en un intercambio busca en los dos operadores, ignorando nombres nulos", () => {
    expect(filaCoincide(par, "ausente ida")).toBe(true);
    expect(filaCoincide(par, "beto-id")).toBe(true);
    expect(filaCoincide(par, "reemplazo")).toBe(false);
  });

  it("nombra a cada operador del par, con su id si no hay nombre", () => {
    if (par.tipo !== "intercambio") throw new Error("fixture");
    expect(nombreOperadorA(par.intercambio)).toBe("Ausente ida");
    expect(nombreOperadorB(par.intercambio)).toBe("beto-id");
  });
});

describe("payload de edición de un intercambio", () => {
  it("A es el ausente de la ida, B el de la vuelta, y alcance total viaja como null", () => {
    const ida = cob("ida", { motivo: "examen", alcanceTotal: false, alcanceItems: ["f1", "f2"] });
    const vuelta = cob("vuelta", { alcanceTotal: true, alcanceItems: ["ignorado"] });
    expect(intercambioAPayload({ id: "i1", ida, vuelta })).toEqual({
      operadorAId: "aus-ida",
      operadorBId: "aus-vuelta",
      desde: "2026-10-05",
      hasta: "2026-10-09",
      alcanceItemsA: ["f1", "f2"],
      alcanceItemsB: null,
      motivo: "examen",
    });
  });
});
