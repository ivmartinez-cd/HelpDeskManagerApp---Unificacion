import { describe, expect, it } from "vitest";
import type { Incidente } from "../types/liquidaciones";
import { computeRutasCompartidas } from "./rutas-compartidas";

const inc = (id: string, over: Partial<Incidente>): Incidente =>
  ({
    id, fechaCierre: "2026-09-10", cantKmCobrado: 50,
    localidadCliente: null, empresaNombre: null, sucursalNombre: null, ...over,
  }) as Incidente;

describe("incidentes que posiblemente comparten ruta", () => {
  it("marca a los dos incidentes del mismo día en la misma localidad, sin importar mayúsculas ni espacios", () => {
    const ids = computeRutasCompartidas([
      inc("a", { localidadCliente: "Rosario " }),
      inc("b", { localidadCliente: "rosario" }),
      inc("c", { localidadCliente: "Funes" }),
    ]);
    expect([...ids].sort()).toEqual(["a", "b"]);
  });

  it("marca los que van a la misma empresa y sucursal aunque la localidad difiera", () => {
    const ids = computeRutasCompartidas([
      inc("a", { empresaNombre: "ACME", sucursalNombre: "Centro", localidadCliente: "X" }),
      inc("b", { empresaNombre: "acme", sucursalNombre: "centro ", localidadCliente: "Y" }),
      inc("c", { empresaNombre: "ACME", sucursalNombre: "Norte", localidadCliente: "Z" }),
    ]);
    expect([...ids].sort()).toEqual(["a", "b"]);
  });

  it("no cruza incidentes de días distintos", () => {
    const ids = computeRutasCompartidas([
      inc("a", { localidadCliente: "Rosario" }),
      inc("b", { localidadCliente: "Rosario", fechaCierre: "2026-09-11" }),
    ]);
    expect(ids.size).toBe(0);
  });

  it("ignora los incidentes sin cierre o sin km cobrados", () => {
    const ids = computeRutasCompartidas([
      inc("a", { localidadCliente: "Rosario" }),
      inc("b", { localidadCliente: "Rosario", cantKmCobrado: 0 }),
      inc("c", { localidadCliente: "Rosario", fechaCierre: null }),
    ]);
    expect(ids.size).toBe(0);
  });

  it("no considera coincidencia a dos localidades vacías", () => {
    expect(computeRutasCompartidas([inc("a", {}), inc("b", {})]).size).toBe(0);
  });
});
