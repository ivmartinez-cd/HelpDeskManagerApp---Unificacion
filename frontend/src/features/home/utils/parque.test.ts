import { describe, expect, it } from "vitest";
import type { OperadorGroup, Prestador, PrestadoresResumen } from "@/features/prestadores/types/prestadores";
import { FALLBACK_COLOR } from "@/shared/utils/formato-dashboard";
import { agruparParque } from "./parque";

function pst(equipos: number | null, isActive = true): Prestador {
  return {
    id: crypto.randomUUID(),
    sigesEmpresaId: 1,
    denComercial: "PST",
    razonSocial: null,
    cuit: null,
    equipos,
    operadorId: null,
    operadorNombre: null,
    operadorColor: null,
    isActive,
    contactos: [],
  };
}

function grupo(operadorId: string | null, prestadores: Prestador[], color: string | null = "#123456"): OperadorGroup {
  return { operadorId, operadorNombre: operadorId ? `Op ${operadorId}` : null, operadorColor: color, prestadores };
}

function resumen(grupos: OperadorGroup[]): PrestadoresResumen {
  return { totalPrestadores: 0, totalActivos: 0, operadoresConPst: 0, sinAsignar: 0, grupos };
}

describe("parque por operador en Inicio", () => {
  it("suma solo los equipos de los PST activos y cuenta cuántos son", () => {
    const [fila] = agruparParque(resumen([grupo("a", [pst(10), pst(null), pst(99, false)])]));
    expect(fila).toEqual({ id: "a", nombre: "Op a", detalle: "2 PST", color: "#123456", valor: 10 });
  });

  it("omite los operadores sin PST activos", () => {
    expect(agruparParque(resumen([grupo("a", [pst(5, false)]), grupo("b", [])]))).toEqual([]);
  });

  it("ordena por equipos de mayor a menor y deja Sin asignar al final", () => {
    const filas = agruparParque(
      resumen([grupo("chico", [pst(3)]), grupo(null, [pst(500)], null), grupo("grande", [pst(40)])]),
    );
    expect(filas.map((f) => f.id)).toEqual(["grande", "chico", "sin-asignar"]);
    expect(filas[2]).toMatchObject({ nombre: "Sin asignar", color: FALLBACK_COLOR, valor: 500 });
  });
});
