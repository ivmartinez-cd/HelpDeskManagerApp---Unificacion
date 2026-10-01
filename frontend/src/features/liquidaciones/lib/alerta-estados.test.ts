import { describe, expect, it } from "vitest";
import type { Alerta, EstadoAlerta } from "../types/liquidaciones";
import { ESTADO_ALERTA_TONO, TRANSICIONES_ALERTA, peorTonoActivo } from "./alerta-estados";

const alerta = (estado: EstadoAlerta) => ({ estado }) as Alerta;

describe("tono de la fila de un incidente según sus alertas", () => {
  it("toma pendiente como el peor estado activo, por encima de en revisión", () => {
    expect(peorTonoActivo([alerta("en_revision"), alerta("pendiente")])).toBe(ESTADO_ALERTA_TONO.pendiente);
  });

  it("usa en revisión cuando no queda ninguna pendiente", () => {
    expect(peorTonoActivo([alerta("resuelta"), alerta("en_revision")])).toBe(ESTADO_ALERTA_TONO.en_revision);
  });

  it("no pinta la fila si todas están resueltas o descartadas, o no hay alertas", () => {
    expect(peorTonoActivo([alerta("resuelta"), alerta("descartada")])).toBeNull();
    expect(peorTonoActivo([])).toBeNull();
  });
});

describe("transiciones de estado de una alerta", () => {
  const destinos = (e: EstadoAlerta) => TRANSICIONES_ALERTA[e].map((t) => t.estado);

  it("desde pendiente se puede revisar, resolver o descartar", () => {
    expect(destinos("pendiente")).toEqual(["en_revision", "resuelta", "descartada"]);
  });

  it("desde en revisión solo se resuelve o descarta", () => {
    expect(destinos("en_revision")).toEqual(["resuelta", "descartada"]);
  });

  it("las cerradas solo se reabren, volviendo a en revisión", () => {
    expect(TRANSICIONES_ALERTA.resuelta).toEqual([{ estado: "en_revision", label: "Reabrir" }]);
    expect(TRANSICIONES_ALERTA.descartada).toEqual([{ estado: "en_revision", label: "Reabrir" }]);
  });

  it("solo descartar pide justificación", () => {
    const todas = Object.values(TRANSICIONES_ALERTA).flat();
    for (const t of todas) expect(Boolean(t.pideJustificacion)).toBe(t.estado === "descartada");
  });
});
